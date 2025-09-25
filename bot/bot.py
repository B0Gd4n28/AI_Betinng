from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import os, asyncio, datetime as dt, requests, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from src.utils.config import settings
from src.utils.leagues import TOP_COMP_CODES, ODDS_SPORT_KEYS, TOP_N_FOR_UI
from src.fetchers.football_data import get_matches_for_date, get_team_recent_results
from src.fetchers.odds_api import get_odds_for_sport, implied_probs_from_bookmakers
from src.analytics.markets import top_market_picks_for_date, seeded_shuffle_picks, compute_parlay_metrics
from src.utils.matching import teams_match
from src.analytics.probability import probs_from_form, blend_probs, ev_from_probs_odds
from src.analytics.express import greedy_highprob
from src.i18n import tr, LANGS
from src.utils.storage import get_lang, set_lang

def _reply(update, text, reply_markup=None):
    # răspunde corect fie din mesaj normal, fie din callback
    if getattr(update, "message", None):
        return update.message.reply_text(text, reply_markup=reply_markup)
    elif getattr(update, "callback_query", None):
        try:
            return update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        except Exception:
            chat_id = update.effective_chat.id if update.effective_chat else None
            if chat_id:
                return update.get_bot().send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    return None


def today_iso():
    return dt.datetime.now(dt.timezone.utc).date().isoformat()

def compute_form_points(matches: list, team_side: str) -> float:
    """
    Returnează puncte/meci în ultimele 5 jocuri pentru echipă.
    """
    pts = []
    for m in matches or []:
        if m.get("status") not in ("FINISHED", "AWARDED"):
            continue
        score = (m.get("score", {}) or {}).get("fullTime", {}) or {}
        hgoals, agoals = score.get("home", 0) or 0, score.get("away", 0) or 0
        if hgoals > agoals:
            res = 'H'
        elif hgoals < agoals:
            res = 'A'
        else:
            res = 'D'
        # scor simplu: H=3, D=1, A=0 (nu știm sigur dacă echipa era acasă)
        p = 1 if res == 'D' else (3 if res == 'H' else 0)
        pts.append(p)
    if not pts:
        return 1.5
    last = pts[-5:]
    return sum(last) / len(last)



def _kb_main(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(tr(lang,"menu_picks"), callback_data="MENU_TODAY")],
        [InlineKeyboardButton(tr(lang,"menu_markets"), callback_data="MENU_MARKETS")],
        [InlineKeyboardButton(tr(lang,"menu_express"), callback_data="MENU_EXPRESS")],
        [InlineKeyboardButton(tr(lang,"menu_lang"), callback_data="MENU_LANG"),
         InlineKeyboardButton(tr(lang,"menu_help"), callback_data="MENU_HELP")]
    ])

def _kb_lang():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Română", callback_data="LANG_RO"),
                                  InlineKeyboardButton("English", callback_data="LANG_EN"),
                                  InlineKeyboardButton("Русский", callback_data="LANG_RU")]])

def _kb_express(lang, legs=None, min_odds=None, max_odds=None):
    row1 = [InlineKeyboardButton(f'{tr(lang,"legs")}:2', callback_data="EXP_LEGS_2"),
            InlineKeyboardButton(f'3', callback_data="EXP_LEGS_3"),
            InlineKeyboardButton(f'4', callback_data="EXP_LEGS_4")]
    row2 = [InlineKeyboardButton(f'{tr(lang,"min_odds")}:1.8', callback_data="EXP_MIN_1.8"),
            InlineKeyboardButton(f'2.0', callback_data="EXP_MIN_2.0"),
            InlineKeyboardButton(f'2.5', callback_data="EXP_MIN_2.5")]
    row3 = [InlineKeyboardButton(f'{tr(lang,"max_odds")}:3.0', callback_data="EXP_MAX_3.0"),
            InlineKeyboardButton(f'4.0', callback_data="EXP_MAX_4.0"),
            InlineKeyboardButton(f'5.0', callback_data="EXP_MAX_5.0")]
    row4 = [InlineKeyboardButton(tr(lang,"build"), callback_data="EXP_BUILD")]
    return InlineKeyboardMarkup([row1,row2,row3,row4])

def seeded_rng_for_user(user_id: int, date_str: str) -> random.Random:
    """Create deterministic RNG for user-specific diversification"""
    return random.Random(f"{user_id}:{date_str}")


async def send_welcome_animation(update, lang):
    """Try to send welcome animation if assets/welcome.gif exists"""
    try:
        with open("assets/welcome.gif", "rb") as gif_file:
            await update.message.reply_animation(gif_file)
    except FileNotFoundError:
        # Skip animation if file doesn't exist
        pass
    except Exception as e:
        print(f"Error sending welcome animation: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    
    # Try to send welcome animation first
    await send_welcome_animation(update, lang)
    
    # Send rich welcome message
    emoji = tr(lang, "app_name_emoji")
    welcome_msg = [
        tr(lang, "welcome_title", emoji=emoji),
        "",
        tr(lang, "welcome_features"),
        "",
        tr(lang, "welcome_commands"),
        "",
        tr(lang, "welcome_disclaimer")
    ]
    
    await update.message.reply_text(
        "\n".join(welcome_msg), 
        reply_markup=_kb_main(lang)
    )

async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    msgs = tr(lang,"health", fd="OK" if settings.football_data_token else "MISSING",
                        odds="OK" if settings.odds_api_key else "MISSING",
                        gdelt=str(settings.gdelt_enabled))
    await update.message.reply_text(msgs)

async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(tr(lang,"processing"))
    date = today_iso()
    await picks_for_date(update, context, date, lang)

async def picks_for_date(update: Update, context: ContextTypes.DEFAULT_TYPE, date_iso: str, lang: str):
    token = settings.football_data_token
    matches = get_matches_for_date(token, TOP_COMP_CODES, date_iso)
    if not matches:
        await _reply(update, tr(lang, "no_matches"))
        return

    # prefetch odds for all markets (h2h, totals, both_teams_to_score)
    odds_all = {}
    odds_unavailable_global = False
    if settings.odds_api_key:
        for code in set([m["competition"] for m in matches]):
            sport_key = ODDS_SPORT_KEYS.get(code)
            if not sport_key: continue
            try:
                data = get_odds_for_sport(
                    settings.odds_api_key, 
                    sport_key, 
                    regions=settings.odds_regions or "uk,eu", 
                    markets="h2h,totals,both_teams_to_score"
                )
                if data and data[0]:
                    odds_all[code] = data[0]
            except:
                continue
    else:
        odds_unavailable_global = True

    picks = []
    for m in matches:
        home_form = compute_form_points(get_team_recent_results(token, m["home_id"], date_iso), "HOME")
        away_form = compute_form_points(get_team_recent_results(token, m["away_id"], date_iso), "AWAY")
        p_form = probs_from_form(home_form-away_form)

        odds_events = odds_all.get(m["competition"], [])
        odds_probs, odds_tuple = (None, None)
        if odds_events:
            odds_probs, odds_tuple = match_odds_for_fixture(odds_events, m["home_name"], m["away_name"])

        p_comb = blend_probs(odds_probs, p_form, m["home_name"], m["away_name"], w_odds=0.8 if odds_probs else 0.0)
        if not odds_tuple:
            odds_tuple = (max(1.01,1.0/max(1e-6,p_comb[0])),
                          max(1.01,1.0/max(1e-6,p_comb[1])),
                          max(1.01,1.0/max(1e-6,p_comb[2])))
        evs = ev_from_probs_odds(p_comb, odds_tuple)
        idx = int(max(range(3), key=lambda i: p_comb[i]))
        selection = ["Home","Draw","Away"][idx]

        picks.append({
            "match": f'{m["home_name"]} vs {m["away_name"]}',
            "competition": m["competition"],
            "selection": selection,
            "p_est": round(float(p_comb[idx]),3),
            "odds": round(float(odds_tuple[idx]),2),
            "ev": round(float(evs[idx]),3)
        })

    # Sort all picks by quality, then apply user-specific diversification
    picks = sorted(picks, key=lambda x: (x["p_est"], x["ev"]), reverse=True)
    
    # Take top TOP_N_FOR_UI candidates and shuffle deterministically per user
    user_id = update.effective_user.id
    top_picks = seeded_shuffle_picks(picks[:TOP_N_FOR_UI], user_id, date_iso, 2)

    lines = [tr(lang, "today_header", date=date_iso)]
    for p in top_picks:
        lines.append(f'• {p["match"]} — {p["selection"]} | p≈{p["p_est"]} | cote {p["odds"]} | EV {p["ev"]}')
    
    # Add odds unavailability message if needed
    if odds_unavailable_global:
        lines.append("")
        lines.append(tr(lang, "odds_unavailable"))
    
    lines.append("")
    lines.append(tr(lang, "disclaimer"))
    await _reply(update, "\n".join(lines), reply_markup=_kb_main(lang))

async def cmd_markets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Over/Under 2.5 and BTTS markets"""
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(tr(lang,"processing"))
    
    # Parse optional date argument or default to today
    args = context.args
    if args and len(args) > 0:
        date_str = args[0]
        if date_str == "today":
            date_str = today_iso()
        # Validate YYYY-MM-DD format
        try:
            dt.datetime.fromisoformat(date_str)
        except ValueError:
            date_str = today_iso()
    else:
        date_str = today_iso()
    
    await markets_for_date(update, context, date_str, lang)


async def markets_for_date(update: Update, context: ContextTypes.DEFAULT_TYPE, date_iso: str, lang: str):
    """Generate Over/Under and BTTS market picks for a specific date"""
    token = settings.football_data_token
    matches = get_matches_for_date(token, TOP_COMP_CODES, date_iso)
    if not matches:
        await _reply(update, tr(lang, "no_matches"))
        return

    # Fetch odds with extended markets  
    odds_events_by_comp = {}
    odds_unavailable = False
    
    if settings.odds_api_key:
        for code in set([m["competition"] for m in matches]):
            sport_key = ODDS_SPORT_KEYS.get(code)
            if not sport_key:
                continue
            try:
                data = get_odds_for_sport(
                    settings.odds_api_key, 
                    sport_key,
                    regions=settings.odds_regions or "uk,eu",
                    markets="h2h,totals,both_teams_to_score"
                )
                if data and data[0]:
                    odds_events_by_comp[code] = data[0]
            except Exception as e:
                print(f"Error fetching odds for {code}: {e}")
                continue
    else:
        odds_unavailable = True

    if not odds_events_by_comp:
        # No odds available, inform user
        lines = [tr(lang, "markets_header", date=date_iso)]
        lines.append("")
        if odds_unavailable:
            lines.append(tr(lang, "odds_unavailable"))
        else:
            lines.append("ℹ️ Nu sunt disponibile cote pentru piețele O/U și BTTS.")
        lines.append("")
        lines.append(tr(lang, "disclaimer"))
        await _reply(update, "\n".join(lines), reply_markup=_kb_main(lang))
        return

    # Get top market picks
    market_picks = top_market_picks_for_date(matches, odds_events_by_comp, target_line=2.5, top_n=4)
    
    if not market_picks:
        lines = [tr(lang, "markets_header", date=date_iso)]
        lines.append("• Nu s-au găsit picks valide pentru piețele O/U & BTTS")
        lines.append("")
        lines.append(tr(lang, "disclaimer"))
        await _reply(update, "\n".join(lines), reply_markup=_kb_main(lang))
        return

    # Format response
    lines = [tr(lang, "markets_header", date=date_iso)]
    for pick in market_picks:
        lines.append(f'• {pick["match"]} — {pick["market"]}: {pick["selection"]} | p≈{pick["p_est"]} | cote {pick["odds"]} | EV {pick["ev"]}')
    
    lines.append("")
    lines.append(tr(lang, "disclaimer"))
    await _reply(update, "\n".join(lines), reply_markup=_kb_main(lang))
    lang = get_lang(update.effective_user.id)
    context.user_data["exp_cfg"] = {"legs":3, "min":2.0, "max":4.0}
    await update.message.reply_text(tr(lang,"wizard_title"), reply_markup=_kb_express(lang))

def normalize_name(s:str)->str:
    return "".join(ch for ch in s.lower() if ch.isalnum() or ch==' ').strip()

def teams_match_wrapper(a,b):
    from src.utils.matching import teams_match as TM
    return TM(a,b)

def match_odds_for_fixture(odds_events: list, home_name: str, away_name: str):
    for ev in odds_events:
        teams = [normalize_name(x) for x in (ev.get("home_team", ""), ev.get("away_team", ""))]

        if teams_match_wrapper(home_name, teams[0]) and teams_match_wrapper(away_name, teams[1]):
            probs = implied_probs_from_bookmakers(ev)
            odds_tuple = None
            for b in ev.get("bookmakers",[]):
                for mkt in b.get("markets",[]):
                    if mkt.get("key")=="h2h":
                        outs = mkt.get("outcomes",[])
                        price_map = {o["name"]: float(o["price"]) for o in outs if "name" in o and "price" in o}
                        h = price_map.get(ev.get("home_team")) or price_map.get("Home")
                        d = price_map.get("Draw") or price_map.get("X")
                        a = price_map.get(ev.get("away_team")) or price_map.get("Away")
                        if h and a and d:
                            odds_tuple = (h,d,a); break
                if odds_tuple: break
            if not odds_tuple and probs:
                h = max(1.01, 1.0/max(1e-6, probs.get(home_name, probs.get("Home",0.33))))
                d = max(1.01, 1.0/max(1e-6, probs.get("Draw",0.33)))
                a = max(1.01, 1.0/max(1e-6, probs.get(away_name, probs.get("Away",0.33))))
                odds_tuple = (h,d,a)
            return probs, odds_tuple
    return None, None

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    data = q.data

    # menu
    if data == "MENU_TODAY":
        await q.edit_message_text(tr(lang,"processing"))
        await picks_for_date(update, context, today_iso(), lang)
        return
    if data == "MENU_MARKETS":
        await q.edit_message_text(tr(lang,"processing"))
        await markets_for_date(update, context, today_iso(), lang)
        return
    if data == "MENU_EXPRESS":
        context.user_data["exp_cfg"] = {"legs":3, "min":2.0, "max":4.0}
        await q.edit_message_text(tr(lang,"wizard_title"), reply_markup=_kb_express(lang))
        return
    if data == "MENU_LANG":
        await q.edit_message_text(tr(lang,"choose_lang"), reply_markup=_kb_lang())
        return
    if data == "MENU_HELP":
        await q.edit_message_text(tr(lang,"help"), reply_markup=_kb_main(lang))
        return

    # language
    if data.startswith("LANG_"):
        lang_code = data.split("_")[1]
        set_lang(user_id, lang_code)
        lang = lang_code
        await q.edit_message_text(tr(lang,"lang_set", lang=lang_code), reply_markup=_kb_main(lang))
        return

    # express wizard
    cfg = context.user_data.get("exp_cfg", {"legs":3, "min":2.0, "max":4.0})
    if data.startswith("EXP_LEGS_"):
        cfg["legs"] = int(data.split("_")[2])
        context.user_data["exp_cfg"] = cfg
        await q.edit_message_reply_markup(_kb_express(lang))
        return
    if data.startswith("EXP_MIN_"):
        cfg["min"] = float(data.split("_")[2])
        context.user_data["exp_cfg"] = cfg
        await q.edit_message_reply_markup(_kb_express(lang))
        return
    if data.startswith("EXP_MAX_"):
        cfg["max"] = float(data.split("_")[2])
        context.user_data["exp_cfg"] = cfg
        await q.edit_message_reply_markup(_kb_express(lang))
        return
    if data == "EXP_BUILD":
        await q.edit_message_text(tr(lang,"processing"))
        await build_express(update, context, lang)
        return

async def cmd_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(tr(lang,"choose_lang"), reply_markup=_kb_lang())

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(tr(lang,"help"), reply_markup=_kb_main(lang))


async def cmd_express(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced express/parlay command with improved detail display"""
    lang = get_lang(update.effective_user.id)
    
    # Check for command arguments
    args = context.args
    if len(args) >= 3:
        try:
            min_odds = float(args[0])
            max_odds = float(args[1])
            legs = int(args[2])
            context.user_data["exp_cfg"] = {"legs": legs, "min": min_odds, "max": max_odds}
            await update.message.reply_text(tr(lang,"processing"))
            await build_express(update, context, lang)
            return
        except (ValueError, IndexError):
            pass
    
    # Show wizard
    context.user_data["exp_cfg"] = {"legs":3, "min":2.0, "max":4.0}
    await update.message.reply_text(tr(lang,"wizard_title"), reply_markup=_kb_express(lang))


async def build_express(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    """Build enhanced express with detailed leg information and combined metrics"""
    cfg = context.user_data.get("exp_cfg", {"legs":3, "min":2.0, "max":4.0})
    
    date_iso = today_iso()
    token = settings.football_data_token
    matches = get_matches_for_date(token, TOP_COMP_CODES, date_iso)
    
    if not matches:
        await _reply(update, tr(lang,"no_matches"), reply_markup=_kb_main(lang))
        return
    
    # Fetch odds
    odds_all = {}
    odds_unavailable = False
    if settings.odds_api_key:
        for code in set([m["competition"] for m in matches]):
            sport_key = ODDS_SPORT_KEYS.get(code)
            if not sport_key: continue
            try:
                data = get_odds_for_sport(
                    settings.odds_api_key, 
                    sport_key, 
                    regions=settings.odds_regions or "uk,eu", 
                    markets="h2h,totals,both_teams_to_score"
                )
                if data and data[0]:
                    odds_all[code] = data[0]
            except:
                continue
    else:
        odds_unavailable = True

    # Build candidate picks
    picks = []
    for m in matches:
        home_form = compute_form_points(get_team_recent_results(token, m["home_id"], date_iso), "HOME")
        away_form = compute_form_points(get_team_recent_results(token, m["away_id"], date_iso), "AWAY")
        p_form = probs_from_form(home_form-away_form)

        odds_events = odds_all.get(m["competition"], [])
        odds_probs, odds_tuple = (None, None)
        if odds_events:
            odds_probs, odds_tuple = match_odds_for_fixture(odds_events, m["home_name"], m["away_name"])

        p_comb = blend_probs(odds_probs, p_form, m["home_name"], m["away_name"], w_odds=0.8 if odds_probs else 0.0)
        if not odds_tuple:
            odds_tuple = (max(1.01,1.0/max(1e-6,p_comb[0])),
                          max(1.01,1.0/max(1e-6,p_comb[1])),
                          max(1.01,1.0/max(1e-6,p_comb[2])))
        idx = int(max(range(3), key=lambda i: p_comb[i]))
        selection = ["Home","Draw","Away"][idx]
        o_sel = odds_tuple[idx]
        picks.append({
            "match": f'{m["home_name"]} vs {m["away_name"]}', 
            "selection": selection, 
            "p_est": float(max(p_comb)), 
            "odds": float(o_sel)
        })

    # Apply user-specific diversification to candidate pool before greedy selection  
    user_id = update.effective_user.id
    diversified_picks = seeded_shuffle_picks(picks, user_id, date_iso, min(len(picks), TOP_N_FOR_UI * 2))
    
    # Run greedy algorithm on diversified pool
    parlay = greedy_highprob(diversified_picks, cfg["min"], cfg["max"], max_legs=cfg["legs"])
    
    if not parlay:
        await _reply(update, tr(lang,"express_fail"), reply_markup=_kb_main(lang))
        return

    # Enhanced display with per-leg details and combined metrics
    lines = [tr(lang,"express_header", date=date_iso, legs=len(parlay["legs_detail"]))]
    lines.append("")
    
    # Show each leg with detailed info
    for i, leg in enumerate(parlay["legs_detail"], 1):
        market_label = "1X2"  # Currently only H2H, can extend later
        lines.append(f'• {leg["match"]} — {market_label}: {leg["selection"]} | p≈{leg["p_est"]:.3f} | cote {leg["odds"]:.2f}')
    
    # Calculate and display combined metrics using new function
    combined = compute_parlay_metrics(parlay["legs_detail"])
    lines.append("")
    lines.append(tr(lang, "express_combined", 
                   prob=combined["combined_prob"], 
                   odds=combined["combined_odds"], 
                   ev=combined["ev"]))
    
    # Add odds unavailability notice if needed
    if odds_unavailable:
        lines.append("")
        lines.append(tr(lang, "odds_unavailable"))
    
    lines.append("")
    lines.append(tr(lang, "disclaimer"))
    
    await _reply(update, "\n".join(lines), reply_markup=_kb_main(lang))


def main():
    token = settings.telegram_token or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", cmd_today))
    app.add_handler(CommandHandler("markets", cmd_markets))
    app.add_handler(CommandHandler("express", cmd_express))
    app.add_handler(CommandHandler("lang", cmd_lang))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("health", health))
    app.add_handler(CallbackQueryHandler(on_callback))
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
