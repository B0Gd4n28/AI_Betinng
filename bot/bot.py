from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import os, asyncio, datetime as dt, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from src.utils.config import settings
from src.utils.leagues import TOP_COMP_CODES, ODDS_SPORT_KEYS
from src.fetchers.football_data import get_matches_for_date, get_team_recent_results
from src.fetchers.odds_api import get_odds_for_sport, implied_probs_from_bookmakers
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


DISCLAIMER = {
    "RO": "⚠️ Pariurile implică risc. +18. Nu există garanții. Joacă responsabil.",
    "EN": "⚠️ Betting involves risk. 18+. No guarantees. Play responsibly.",
    "RU": "⚠️ Азартные игры несут риск. 18+. Гарантий нет. Играйте ответственно."
}

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
        [InlineKeyboardButton(tr(lang,"menu_express"), callback_data="MENU_EXPRESS")],
        [InlineKeyboardButton(tr(lang,"menu_lang"), callback_data="MENU_LANG")],
        [InlineKeyboardButton(tr(lang,"menu_help"), callback_data="MENU_HELP")]
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(tr(lang,"start"), reply_markup=_kb_main(lang))

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

    # prefetch odds
    odds_all = {}
    if settings.odds_api_key:
        for code in set([m["competition"] for m in matches]):
            sport_key = ODDS_SPORT_KEYS.get(code)
            if not sport_key: continue
            data = get_odds_for_sport(settings.odds_api_key, sport_key, regions=settings.odds_regions, markets=settings.odds_markets)
            if not data: continue
            odds_all[code] = data[0]

    picks=[]
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

    picks = sorted(picks, key=lambda x: (x["p_est"], x["ev"]), reverse=True)[:20]
    lines = [tr(lang,"today_header", date=date_iso, n=len(picks))]
    for p in picks[:10]:
        lines.append(f'• {p["match"]} ({p["competition"]}) — {p["selection"]} | p≈{p["p_est"]} | cote {p["odds"]} | EV {p["ev"]}')
    lines.append("\n"+DISCLAIMER.get(lang, DISCLAIMER["EN"]))
    await _reply(update, "\n".join(lines), reply_markup=_kb_main(lang))

async def cmd_express(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        # build & display
        date_iso = today_iso()
        token = settings.football_data_token
        matches = get_matches_for_date(token, TOP_COMP_CODES, date_iso)
        if not matches:
            await q.edit_message_text(tr(lang,"no_matches"), reply_markup=_kb_main(lang))
            return
        odds_all={}
        if settings.odds_api_key:
            for code in set([m["competition"] for m in matches]):
                sport_key = ODDS_SPORT_KEYS.get(code)
                if not sport_key: continue
                datao = get_odds_for_sport(settings.odds_api_key, sport_key, regions=settings.odds_regions, markets=settings.odds_markets)
                if not datao: continue
                odds_all[code] = datao[0]

        picks=[]
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
            picks.append({"match": f'{m["home_name"]} vs {m["away_name"]}', "selection": selection, "p_est": float(max(p_comb)), "odds": float(o_sel)})

        parlay = greedy_highprob(picks, cfg["min"], cfg["max"], max_legs=cfg["legs"])
        if not parlay:
            await q.edit_message_text(tr(lang,"express_fail"), reply_markup=_kb_main(lang))
            return
        legs_txt = " + ".join([f'{l["match"]} ({l["selection"]})' for l in parlay["legs_detail"]])
        msg = f'{tr(lang,"express_header", date=date_iso)}\n{legs_txt}\nProb≈{parlay["prob"]:.3f} | Cote totale {parlay["odds"]:.2f} | EV {parlay["ev"]:.3f}\n\n{DISCLAIMER.get(lang, DISCLAIMER["EN"])}'
        await q.edit_message_text(msg, reply_markup=_kb_main(lang))
        return

async def cmd_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(tr(lang,"choose_lang"), reply_markup=_kb_lang())

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(tr(lang,"help"), reply_markup=_kb_main(lang))

def main():
    token = settings.telegram_token or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", cmd_today))
    app.add_handler(CommandHandler("express", cmd_express))
    app.add_handler(CommandHandler("lang", cmd_lang))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("health", health))
    app.add_handler(CallbackQueryHandler(on_callback))
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
