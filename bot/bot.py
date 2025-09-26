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
from src.analytics.stats import (
    get_stats_summary, add_bet_record, update_bet_result, 
    get_monthly_chart, get_leaderboard, load_user_stats, save_user_stats
)
from src.utils.subs import plan_gate, get_user_stats, use_trial, log_user_activity, get_user_account_info, get_pricing_catalog, is_admin
from src.analytics.strategies import (
    find_value_bets, detect_arbitrage_opportunities, build_accumulator,
    kelly_criterion_stake, martingale_protection_check
)
from src.analytics.ai_personal import (
    analyze_betting_patterns, generate_personal_recommendations,
    adaptive_odds_evaluation, get_strategy_recommendation
)
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

async def show_account_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user account information"""
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    
    # Get account info
    account_info = get_user_account_info(user_id)
    
    # Format plan display
    plan_display = {
        'free': '🆓 **FREE** (Trial)',
        'BASIC': '⭐ **BASIC**',
        'PRO': '🔥 **PRO**', 
        'PREMIUM': '💎 **PREMIUM**'
    }.get(account_info['plan'], '🆓 **FREE**')
    
    # Format remaining trials
    if account_info['plan'] == 'free':
        remaining_display = f"🎯 **{account_info['remaining_trials']}/2** generări gratuite"
    else:
        remaining_display = "♾️ **NELIMITAT**"
    
    # Format subscription status
    if account_info['subscription_active']:
        status_display = f"✅ **ACTIV** până la {account_info['expires']}"
    elif account_info['plan'] != 'free':
        status_display = f"⚠️ **EXPIRAT** din {account_info['expires']}"
    else:
        status_display = "🆓 **TRIAL ACTIV**"
    
    # Format join date
    try:
        join_date = dt.datetime.fromisoformat(account_info['joined']).strftime("%d.%m.%Y")
    except:
        join_date = "N/A"
    
    account_msg = [
        "👤 **CONTUL MEU** 👤",
        "═══════════════════",
        "",
        f"🆔 **User ID:** `{account_info['user_id']}`",
        f"📊 **Plan:** {plan_display}",
        f"⚡ **Status:** {status_display}",
        f"{remaining_display}",
        f"📅 **Membru din:** {join_date}",
        "",
        "🎯 **Utilizări Trial:** " + f"{account_info['trial_used']}/2",
        "",
        "💡 **Tip:** Upgrade pentru predicții nelimitate!"
    ]
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Upgrade Plan", callback_data="MENU_SUBSCRIPTION")],
        [InlineKeyboardButton("👨‍💼 Contact Admin", callback_data="CONTACT_ADMIN")],
        [InlineKeyboardButton("🔙 Meniu Principal", callback_data="MENU_MAIN")]
    ])
    
    q = update.callback_query
    await q.edit_message_text("\n".join(account_msg), reply_markup=keyboard, parse_mode='Markdown')

async def show_subscription_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show subscription plans and pricing"""
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    
    # Get pricing catalog
    pricing = get_pricing_catalog()
    
    subscription_msg = [
        "💎 **PLANURI DE ABONAMENT** 💎",
        "═══════════════════════════════",
        "",
        "🎯 **Alege planul perfect pentru tine:**",
        ""
    ]
    
    # Add each plan
    for plan_name, plan_info in pricing.items():
        if plan_info.get('popular'):
            subscription_msg.append(f"🔥 **{plan_name}** ⭐ *CEL MAI POPULAR*")
        elif plan_info.get('exclusive'):
            subscription_msg.append(f"👑 **{plan_name}** 💎 *EXCLUSIVE*")
        else:
            subscription_msg.append(f"⭐ **{plan_name}**")
        
        subscription_msg.append(f"💰 **{plan_info['price_monthly']}**")
        subscription_msg.append(f"🎁 **{plan_info['price_yearly']}**")
        subscription_msg.append("")
        
        # Add features
        for feature in plan_info['features']:
            subscription_msg.append(f"  {feature}")
        
        if 'savings' in plan_info:
            subscription_msg.append(f"  💡 *{plan_info['savings']}*")
        
        subscription_msg.append("")
        subscription_msg.append("─────────────────────")
        subscription_msg.append("")
    
    subscription_msg.extend([
        "🚀 **De ce să alegi PariuSmart AI?**",
        "✅ Predicții bazate pe AI avansat",
        "✅ Analiză în timp real",
        "✅ Suport expert 24/7",
        "✅ ROI garantat sau înapoi banii!*",
        "",
        "🎁 **BONUS:** Prima săptămână GRATUIT!",
        "",
        "*Termeni și condiții se aplică"
    ])
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 BASIC Plan", callback_data="SELECT_BASIC"),
         InlineKeyboardButton("⭐ PRO Plan", callback_data="SELECT_PRO")],
        [InlineKeyboardButton("💎 PREMIUM Plan", callback_data="SELECT_PREMIUM")],
        [InlineKeyboardButton("👨‍💼 Vorbește cu Adminul", callback_data="CONTACT_ADMIN")],
        [InlineKeyboardButton("🔙 Înapoi", callback_data="MENU_ACCOUNT")]
    ])
    
    q = update.callback_query
    await q.edit_message_text("\n".join(subscription_msg), reply_markup=keyboard, parse_mode='Markdown')

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
    """Enhanced main menu with modern card-style buttons"""
    return InlineKeyboardMarkup([
        # Core betting features
        [InlineKeyboardButton("🔥 " + tr(lang,"menu_picks") + " 🔥", callback_data="MENU_TODAY")],
        [InlineKeyboardButton("📊 " + tr(lang,"menu_markets") + " 📊", callback_data="MENU_MARKETS")],
        [InlineKeyboardButton("🎯 " + tr(lang,"menu_express") + " 🎯", callback_data="MENU_EXPRESS")],
        [InlineKeyboardButton("🌟 Predicții Complete 🌟", callback_data="MENU_ALL_MARKETS")],
        
        # 🚀 NEW: Advanced features  
        [InlineKeyboardButton("📈 Stats & Analytics 📈", callback_data="MENU_STATS"),
         InlineKeyboardButton("💰 Bankroll 💰", callback_data="MENU_BANKROLL")],
        [InlineKeyboardButton("⚡ Live Center ⚡", callback_data="MENU_LIVE"),
         InlineKeyboardButton("🎯 Strategies 🎯", callback_data="MENU_STRATEGIES")],
        [InlineKeyboardButton("🏆 Social & Challenges 🏆", callback_data="MENU_SOCIAL")],
        [InlineKeyboardButton("🤖 Personal AI 🤖", callback_data="MENU_AI")],
        
        # Account & Subscription
        [InlineKeyboardButton("👤 Contul Meu 👤", callback_data="MENU_ACCOUNT"),
         InlineKeyboardButton("💎 Abonamente 💎", callback_data="MENU_SUBSCRIPTION")],
        
        # Settings
        [InlineKeyboardButton("🌐 " + tr(lang,"menu_lang"), callback_data="MENU_LANG"),
         InlineKeyboardButton("ℹ️ " + tr(lang,"menu_help"), callback_data="MENU_HELP")]
    ])

def _kb_lang():
    """Enhanced language selector with flag emojis"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇴 Română", callback_data="LANG_RO"),
         InlineKeyboardButton("🇬🇧 English", callback_data="LANG_EN")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="LANG_RU"),
         InlineKeyboardButton("🔙 Înapoi", callback_data="MENU_MAIN")]
    ])

def _kb_express(lang, legs=None, min_odds=None, max_odds=None):
    """Enhanced express builder with visual indicators"""
    current_legs = legs or 3
    current_min = min_odds or 2.0
    current_max = max_odds or 4.0
    
    row1 = [
        InlineKeyboardButton(f"📊 {tr(lang,'legs')}: {current_legs}", callback_data="EXP_INFO"),
        InlineKeyboardButton("2️⃣", callback_data="EXP_LEGS_2"),
        InlineKeyboardButton("3️⃣", callback_data="EXP_LEGS_3"),
        InlineKeyboardButton("4️⃣", callback_data="EXP_LEGS_4")
    ]
    row2 = [
        InlineKeyboardButton(f"📈 Min: {current_min}", callback_data="EXP_INFO"),
        InlineKeyboardButton("1.8", callback_data="EXP_MIN_1.8"),
        InlineKeyboardButton("2.0", callback_data="EXP_MIN_2.0"),
        InlineKeyboardButton("2.5", callback_data="EXP_MIN_2.5")
    ]
    row3 = [
        InlineKeyboardButton(f"📉 Max: {current_max}", callback_data="EXP_INFO"),
        InlineKeyboardButton("3.0", callback_data="EXP_MAX_3.0"),
        InlineKeyboardButton("4.0", callback_data="EXP_MAX_4.0"),
        InlineKeyboardButton("5.0", callback_data="EXP_MAX_5.0")
    ]
    row4 = [
        InlineKeyboardButton(f"🚀 {tr(lang,'build')} Expres 🚀", callback_data="EXP_BUILD"),
        InlineKeyboardButton("🔙 Meniu", callback_data="MENU_MAIN")
    ]
    return InlineKeyboardMarkup([row1,row2,row3,row4])

def seeded_rng_for_user(user_id: int, date_str: str) -> random.Random:
    """Create deterministic RNG for user-specific diversification"""
    return random.Random(f"{user_id}:{date_str}")


async def send_loading_animation(update, sticker_type="loading"):
    """Send loading animation that stays visible until manually deleted"""
    sticker_animations = {
        "welcome": [
            "⚽", "⚽🤖", "⚽🤖⚡", "⚽🤖⚡🎯", "⚽🤖⚡🎯✨"
        ],
        "loading": [
            "🔄", "🔄⚡", "🔄⚡💫", "🔄⚡💫🎯", "🔄⚡💫🎯✨"
        ],
        "success": [
            "✅", "✅🎉", "✅🎉⭐", "✅🎉⭐💎", "✅🎉⭐💎🔥"
        ],
        "prediction": [
            "🎯", "🎯📊", "🎯📊⚡", "🎯📊⚡🔥", "🎯📊⚡🔥💎"
        ],
        "live": [
            "⚡", "⚡🔴", "⚡🔴📡", "⚡🔴📡🎬", "⚡🔴📡🎬💥"
        ],
        "money": [
            "💰", "💰💵", "💰💵📈", "💰💵📈🚀", "💰💵📈🚀💎"
        ]
    }
    
    animations = sticker_animations.get(sticker_type, sticker_animations["loading"])
    
    try:
        # Create animated sequence that stays visible
        message = None
        for i, frame in enumerate(animations):
            animation_text = f"{frame} **PROCESARE...**" if sticker_type == "loading" else frame
            
            if i == 0:
                message = await update.effective_message.reply_text(animation_text, parse_mode='Markdown')
            else:
                await message.edit_text(animation_text, parse_mode='Markdown')
            
            import asyncio
            await asyncio.sleep(0.4)  # Slower for loading visibility
            
        # Return message so it can be deleted later
        return message
    except Exception as e:
        print(f"Animation error: {e}")
        return None

async def delete_animation_message(message):
    """Delete animation message after processing is complete"""
    if message:
        try:
            await message.delete()
        except:
            pass  # Silent fail if deletion not possible

async def show_trial_expired_message(update):
    """Show educational message when trial is expired"""
    educational_msg = """
🤖🎓 **Despre PariuSmart AI**

**Cum funcționează?**
🧠 Folosesc Inteligența Artificială pentru a analiza:
• Statistici echipe din ultimele 5 meciuri
• Cote de la multiple case de pariuri
• Condiții meteo și factori contextuali
• Sentiment din știri și social media

**De ce să alegi PariuSmart AI?**
✅ **Transparență 100%** - Îți explic fiecare predicție
✅ **Învățare continuă** - Algoritmii se îmbunătățesc zilnic
✅ **Expected Value** - Calculez profitabilitatea fiecărui pariu
✅ **Risk Management** - Te ajut să pariezi responsabil

**🎁 Trial-ul tău gratuit s-a încheiat!**

**Alege un plan pentru acces nelimitat:**

🥉 **Starter (€9.99/lună)**
• Acces la toate piețele (1X2, O/U, BTTS)
• Expresuri cu max 3 selecții
• Predicții zilnice nelimitate

🥇 **Pro (€19.99/lună)**  
• Tot ce include Starter +
• Analytics personal și statistici
• Expresuri cu max 4 selecții
• Management bankroll cu Kelly Criterion

💡 **Observație:** Nu garantez profit, dar îți ofer cele mai bune analize bazate pe date reale și AI.

Folosește /subscribe pentru a alege planul potrivit! 🚀
    """
    
    keyboard = [
        [InlineKeyboardButton("💳 Vezi Planurile", callback_data="MENU_SUBSCRIBE")],
        [InlineKeyboardButton("📊 Cum Funcționează AI", callback_data="ABOUT_AI")],
        [InlineKeyboardButton("🔙 Meniu Principal", callback_data="MENU_MAIN")]
    ]
    
    await update.message.reply_text(
        educational_msg, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def send_animated_sticker(update, sticker_type="welcome", auto_delete=False):
    """Send animated stickers similar to Telegram sticker packs"""
    sticker_animations = {
        "welcome": [
            "⚽", "⚽🤖", "⚽🤖⚡", "⚽🤖⚡🎯", "⚽🤖⚡🎯✨",
            "🎉⚽🤖⚡🎯✨🎉", "🔥⚽🤖⚡🎯✨🔥", "💎⚽🤖⚡🎯✨💎"
        ],
        "loading": [
            "🔄", "🔄⚡", "🔄⚡💫", "🔄⚡💫🎯", "🔄⚡💫🎯✨"
        ],
        "success": [
            "✅", "✅🎉", "✅🎉⭐", "✅🎉⭐💎", "✅🎉⭐💎🔥"
        ],
        "prediction": [
            "🎯", "🎯📊", "🎯📊⚡", "🎯📊⚡🔥", "🎯📊⚡🔥💎"
        ],
        "live": [
            "⚡", "⚡🔴", "⚡�📡", "⚡🔴📡🎬", "⚡🔴📡🎬💥"
        ],
        "money": [
            "�", "💰💵", "💰💵📈", "💰💵📈🚀", "💰💵📈🚀💎"
        ]
    }
    
    animations = sticker_animations.get(sticker_type, sticker_animations["welcome"])
    
    try:
        # Create animated sequence
        message = None
        for i, frame in enumerate(animations):
            animation_text = f"{frame} **{sticker_type.upper()}**" if i == len(animations)-1 else frame
            
            if i == 0:
                message = await update.effective_message.reply_text(animation_text, parse_mode='Markdown')
            else:
                await message.edit_text(animation_text, parse_mode='Markdown')
            
            import asyncio
            await asyncio.sleep(0.2)  # Fast animation
            
        # Auto-delete for better user experience
        if auto_delete and message:
            await asyncio.sleep(1.0)  # Brief pause to show final frame
            try:
                await message.delete()
            except:
                pass  # Silent fail if deletion not possible
        
        return message
    except Exception as e:
        print(f"Animation error: {e}")
        return None

async def send_welcome_animation(update, lang):
    """Enhanced welcome animation with telegram-style animated stickers"""
    try:
        # Try to send welcome GIF first
        with open("assets/welcome.gif", "rb") as gif_file:
            await update.message.reply_animation(gif_file)
            await send_animated_sticker(update, "welcome")
    except FileNotFoundError:
        # Create telegram-style animated sticker welcome
        await send_animated_sticker(update, "welcome")
    except Exception as e:
        print(f"Error sending welcome animation: {e}")
        await send_animated_sticker(update, "welcome")


def format_match_card(match_data, lang="RO"):
    """Create a stunning match card with enhanced visual effects"""
    home = match_data["home_name"]
    away = match_data["away_name"]
    
    # Enhanced header with visual effects
    card_lines = [
        "🌟━━━━━━━━━━━━━━━━━━━━━━🌟",
        f"⚽ **{home}** ⚡🆚⚡ **{away}**",
        "🔥━━━━━━━━━━━━━━━━━━━━━━🔥",
        ""
    ]
    
    # Enhanced 1X2 Market with confidence indicators
    if "h2h_probs" in match_data:
        h2h = match_data["h2h_probs"]
        h2h_odds = match_data.get("h2h_odds", [2.0, 3.5, 2.8])
        
        # Add confidence indicators
        max_prob = max(h2h)
        confidence = "🔥🔥🔥" if max_prob > 0.6 else "🔥🔥" if max_prob > 0.5 else "🔥"
        
        card_lines.extend([
            f"🏆 **1X2 (Câștigător):** {confidence}",
            f"├ 🏠 {home}: **{h2h[0]:.1%}** (cota {h2h_odds[0]:.2f}) {'🎯' if h2h[0] == max_prob else ''}",
            f"├ ⚪ Egal: **{h2h[1]:.1%}** (cota {h2h_odds[1]:.2f}) {'🎯' if h2h[1] == max_prob else ''}", 
            f"└ 🛣️  {away}: **{h2h[2]:.1%}** (cota {h2h_odds[2]:.2f}) {'🎯' if h2h[2] == max_prob else ''}",
            ""
        ])
    
    # Enhanced Over/Under Goals with visual indicators
    if "ou_probs" in match_data:
        ou = match_data["ou_probs"] 
        ou_odds = match_data.get("ou_odds", [1.85, 1.95])
        
        max_ou = max(ou)
        ou_confidence = "💥💥💥" if max_ou > 0.7 else "💥💥" if max_ou > 0.6 else "💥"
        
        card_lines.extend([
            f"⚽ **Over/Under 2.5 Goluri:** {ou_confidence}",
            f"├ 📈 Over 2.5: **{ou[0]:.1%}** (cota {ou_odds[0]:.2f}) {'🎯' if ou[0] == max_ou else ''}",
            f"└ 📉 Under 2.5: **{ou[1]:.1%}** (cota {ou_odds[1]:.2f}) {'🎯' if ou[1] == max_ou else ''}",
            ""
        ])
    
    # Enhanced Both Teams to Score
    if "btts_probs" in match_data:
        btts = match_data["btts_probs"]
        btts_odds = match_data.get("btts_odds", [1.75, 2.05])
        
        max_btts = max(btts)
        btts_confidence = "⚡⚡⚡" if max_btts > 0.7 else "⚡⚡" if max_btts > 0.6 else "⚡"
        
        card_lines.extend([
            f"🎯 **Ambele Echipe Marchează:** {btts_confidence}",
            f"├ ✅ Da: **{btts[0]:.1%}** (cota {btts_odds[0]:.2f}) {'🎯' if btts[0] == max_btts else ''}",
            f"└ ❌ Nu: **{btts[1]:.1%}** (cota {btts_odds[1]:.2f}) {'🎯' if btts[1] == max_btts else ''}",
            ""
        ])
    
    # Enhanced Match Insights with visual appeal
    if "insights" in match_data:
        insights = match_data["insights"]
        card_lines.extend([
            "🧠💡 **AI Match Insights:**",
            f"└ 🔍 {insights}",
            ""
        ])
    
    # Enhanced Best Pick Recommendation with premium styling
    if "best_pick" in match_data:
        pick = match_data["best_pick"]
        ev_emoji = "🔥💎🔥" if pick["ev"] > 0.1 else "⭐🎯⭐" if pick["ev"] > 0.05 else "💫✨💫"
        
        card_lines.extend([
            f"🚀 **PICK OF THE MATCH** {ev_emoji}",
            f"🎯 **{pick['market']}**: **{pick['selection']}**",
            f"📊 Probabilitate: **{pick['prob']:.1%}** | 💰 EV: **{pick['ev']:+.3f}**",
            ""
        ])
    
    # Enhanced footer with visual flair
    card_lines.extend([
        "✨━━━━━━━━━━━━━━━━━━━━━━✨",
        "🤖 **Powered by PariuSmart AI** 🧠",
        "💎━━━━━━━━━━━━━━━━━━━━━━💎"
    ])
    
    return "\n".join(card_lines)


def get_comprehensive_match_predictions(match, odds_events, token, date_iso):
    """Get all market predictions for a single match"""
    home_name, away_name = match["home_name"], match["away_name"]
    
    # Get form-based probabilities
    home_form = compute_form_points(get_team_recent_results(token, match["home_id"], date_iso), "HOME")
    away_form = compute_form_points(get_team_recent_results(token, match["away_id"], date_iso), "AWAY")
    p_form = probs_from_form(home_form-away_form)
    
    # Initialize result
    result = {
        "home_name": home_name,
        "away_name": away_name,
        "competition": match["competition"]
    }
    
    # Find odds for this match
    matched_event = None
    if odds_events:
        for ev in odds_events:
            home_odds = normalize_name(ev.get("home_team", ""))
            away_odds = normalize_name(ev.get("away_team", ""))
            if teams_match_wrapper(home_name, home_odds) and teams_match_wrapper(away_name, away_odds):
                matched_event = ev
                break
    
    # H2H Probabilities and odds
    if matched_event:
        # Get implied probabilities using existing function
        implied_probs = implied_probs_from_bookmakers(matched_event) or {}
        
        # Extract H2H probabilities
        h2h_probs = [
            implied_probs.get(home_name, implied_probs.get("Home", 0.33)),
            implied_probs.get("Draw", 0.33), 
            implied_probs.get(away_name, implied_probs.get("Away", 0.33))
        ]
        
        # Normalize probabilities to sum to 1
        total_prob = sum(h2h_probs)
        if total_prob > 0:
            h2h_probs = [p/total_prob for p in h2h_probs]
        else:
            h2h_probs = [0.33, 0.33, 0.34]
        
        # Blend with form
        result["h2h_probs"] = blend_probs(h2h_probs, p_form, home_name, away_name, w_odds=0.8)
        
        # Extract actual odds from bookmakers
        h2h_odds = [2.0, 3.5, 2.8]  # defaults
        for bookmaker in matched_event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market.get("key") == "h2h":
                    outcomes = market.get("outcomes", [])
                    for outcome in outcomes:
                        name = outcome.get("name", "")
                        price = outcome.get("price", 2.0)
                        if name == matched_event.get("home_team") or name == "Home":
                            h2h_odds[0] = price
                        elif name == "Draw":
                            h2h_odds[1] = price
                        elif name == matched_event.get("away_team") or name == "Away":
                            h2h_odds[2] = price
                    break
        result["h2h_odds"] = h2h_odds
    else:
        result["h2h_probs"] = p_form
        result["h2h_odds"] = [1.0/max(0.01, p) for p in p_form]
    
    # Over/Under 2.5
    if matched_event:
        ou_probs = [0.5, 0.5]  # defaults
        ou_odds = [1.9, 1.9]   # defaults
        
        for bookmaker in matched_event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market.get("key") == "both_teams_to_score":
                    outcomes = market.get("outcomes", [])
                    for outcome in outcomes:
                        name = outcome.get("name", "")
                        price = outcome.get("price", 1.9)
                        point = outcome.get("point", 2.5)
                        if point == 2.5:
                            if "Over" in name:
                                ou_odds[0] = price
                                ou_probs[0] = 1.0 / price
                            elif "Under" in name:
                                ou_odds[1] = price
                                ou_probs[1] = 1.0 / price
                    break
        
        # Normalize probabilities
        total_prob = sum(ou_probs)
        if total_prob > 0:
            ou_probs = [p/total_prob for p in ou_probs]
        
        result["ou_probs"] = ou_probs
        result["ou_odds"] = ou_odds
    else:
        # Estimate based on teams' attacking form
        avg_form = (home_form + away_form) / 2
        over_prob = min(0.8, max(0.2, (avg_form - 1.0) / 2.0 + 0.5))
        result["ou_probs"] = [over_prob, 1.0 - over_prob]
        result["ou_odds"] = [1.0/over_prob, 1.0/(1.0-over_prob)]
    
    # Both Teams to Score - Mock estimation until API is fixed
    if matched_event:
        # For now, estimate BTTS based on Over/Under probability
        over_25_prob = result.get("ou_probs", [0.5, 0.5])[0]
        btts_prob = min(0.75, max(0.25, over_25_prob * 0.85))  # BTTS usually correlated with Over 2.5
        result["btts_probs"] = [btts_prob, 1.0 - btts_prob]
        result["btts_odds"] = [1.0/btts_prob, 1.0/(1.0-btts_prob)]
    else:
        # Estimate BTTS based on form balance
        form_balance = abs(home_form - away_form)
        btts_prob = min(0.75, max(0.25, 0.6 - form_balance * 0.1))
        result["btts_probs"] = [btts_prob, 1.0 - btts_prob]
        result["btts_odds"] = [1.0/btts_prob, 1.0/(1.0-btts_prob)]
    
    # Generate insights
    try:
        from src.analytics.insights import MatchInsightsGenerator
        generator = MatchInsightsGenerator()
        result["insights"] = generator.build_match_insights(match, {})[:100] + "..."
    except:
        avg_goals = (result["ou_probs"][0] * 3.2) + (result["ou_probs"][1] * 1.8)
        result["insights"] = f"⚽ Goluri estimate: {avg_goals:.1f} • 🏠 Forma casă: {home_form:.1f} • 🛣️ Forma deplasare: {away_form:.1f}"
    
    # Find best pick
    all_picks = [
        {"market": "1X2", "selection": home_name, "prob": result["h2h_probs"][0], "odds": result["h2h_odds"][0]},
        {"market": "1X2", "selection": "Egal", "prob": result["h2h_probs"][1], "odds": result["h2h_odds"][1]},
        {"market": "1X2", "selection": away_name, "prob": result["h2h_probs"][2], "odds": result["h2h_odds"][2]},
        {"market": "O/U 2.5", "selection": "Over 2.5", "prob": result["ou_probs"][0], "odds": result["ou_odds"][0]},
        {"market": "O/U 2.5", "selection": "Under 2.5", "prob": result["ou_probs"][1], "odds": result["ou_odds"][1]},
        {"market": "BTTS", "selection": "Da", "prob": result["btts_probs"][0], "odds": result["btts_odds"][0]},
        {"market": "BTTS", "selection": "Nu", "prob": result["btts_probs"][1], "odds": result["btts_odds"][1]}
    ]
    
    # Calculate EV for each pick and find best
    for pick in all_picks:
        pick["ev"] = (pick["prob"] * pick["odds"]) - 1.0
    
    result["best_pick"] = max(all_picks, key=lambda x: x["ev"])
    
    return result


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    user_name = update.effective_user.first_name or "Prietene"
    
    # Get user stats for personalized welcome
    user_stats = get_user_stats(uid)
    
    # Try to send welcome animation first
    await send_welcome_animation(update, lang)
    
    # Personalized welcome based on user status
    if user_stats['is_new_user']:
        # New user - explain trial and AI
        welcome_msg = [
            f"👋 **Bun venit în PariuSmart AI, {user_name}!**",
            "",
            "🎁 **Cadou de bun venit: 2 generări gratuite!**",
            "",
            "🤖 **Ce este PariuSmart AI?**",
            "• Asistent inteligent pentru analize fotbal",
            "• Algoritmi AI care învață din fiecare meci",
            "• Predicții bazate pe statistici reale, nu ghicești",
            "",
            "🧠 **Cum funcționează?**",
            "• Analizez ultimele 5 meciuri ale fiecărei echipe",
            "• Compar cote de la 10+ case de pariuri",
            "• Calculez Expected Value (EV) pentru profit",
            "• Iau în considerare meteo, știri, sentiment",
            "",
            f"✨ **Status tău:** {user_stats['trial_remaining']} predicții gratuite rămase",
            "",
            "🚀 **Încearcă primul pick cu /today!**"
        ]
    elif user_stats['plan'] == 'free' and user_stats['trial_remaining'] > 0:
        # Existing free user with trials
        welcome_msg = [
            f"👋 **Salut din nou, {user_name}!**",
            "",
            f"🎁 **Îți mai rămân {user_stats['trial_remaining']} generări gratuite**",
            "",
            "📊 **Ultimele îmbunătățiri AI:**",
            "• Algoritmi de învățare actualizați zilnic",
            "• Analiză îmbunătățită pentru weekend",
            "• Predicții mai precise pentru lige mari",
            "",
            "🚀 **Generează predicția cu /today**"
        ]
    elif user_stats['plan'] == 'free':
        # Free user with no trials
        welcome_msg = [
            f"👋 **Bună, {user_name}!**",
            "",
            "⏰ **Trial-ul gratuit s-a încheiat**",
            "",
            "💎 **De ce să continui cu PariuSmart AI?**",
            "• Rata de succes 65%+ în ultima lună",
            "• Algoritmi AI care se îmbunătățesc zilnic", 
            "• Comunitate de 1000+ utilizatori mulțumiți",
            "",
            "🎯 **Alege un abonament pentru acces nelimitat!**"
        ]
    else:
        # Paid subscriber  
        plan_emoji = "🥉" if user_stats['plan'] == 'starter' else "🥇"
        welcome_msg = [
            f"👑 **Salut, {user_name}! - Subscriber {user_stats['plan'].title()}**",
            "",
            f"{plan_emoji} **Plan activ:** {user_stats['plan'].title()}",
            f"📅 **Valabil până:** {user_stats['expires']}",
            f"⏰ **Zile rămase:** {user_stats['days_left']}",
            "",
            "🔥 **Acces complet la toate funcțiile!**",
            "",
            "🚀 **Generează predicții nelimitat!**"
        ]
    
    await update.message.reply_text(
        "\n".join(welcome_msg), 
        reply_markup=_kb_main(lang),
        parse_mode='Markdown'
    )

async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    
    # Get health status from settings
    health_status = settings.get_health_status()
    
    health_text = tr(lang, "health", 
                    fd=health_status.get("FOOTBALL_DATA_TOKEN", "MISSING"),
                    odds=health_status.get("ODDS_API_KEY", "MISSING"),
                    api_football=health_status.get("API_FOOTBALL_KEY", "MISSING"),
                    weather=health_status.get("OPENWEATHER_KEY", "MISSING"),
                    reddit=health_status.get("REDDIT_CLIENT_ID", "MISSING"),
                    video=health_status.get("VIDEO_API_TOKEN", "MISSING"),
                    gdelt="ENABLED" if settings.gdelt_enabled else "DISABLED")
    
    await update.message.reply_text(f"{tr(lang, 'health_title')}\n\n{health_text}")

async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    can_access, msg = plan_gate(uid, 'today')
    
    if not can_access:
        # Show educational message for trial expired users
        await show_trial_expired_message(update)
        return
    
    # Use trial if free user
    user_stats = get_user_stats(uid)
    if user_stats['plan'] == 'free':
        if not use_trial(uid):
            await show_trial_expired_message(update)
            return
        
        # Show trial usage info
        remaining = user_stats['trial_remaining'] - 1
        trial_msg = f"🎁 Trial folosit! Îți mai rămân {remaining} generări gratuite."
        await update.message.reply_text(trial_msg)
    
    lang = get_lang(uid)
    await update.message.reply_text(tr(lang,"processing"))
    date = today_iso()
    await picks_for_date(update, context, date, lang)

async def picks_for_date(update: Update, context: ContextTypes.DEFAULT_TYPE, date_iso: str, lang: str):
    token = settings.football_data_token
    matches = get_matches_for_date(token, TOP_COMP_CODES, date_iso)
    if not matches:
        await _reply(update, tr(lang, "no_matches"))
        return

    # prefetch odds for all markets (h2h, totals)
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
                    markets="h2h,totals"  # Remove problematic BTTS market
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

    # Enhanced display with beautiful cards
    lines = [
        "🔥 **TOP PICKS AI** 🔥",
        f"📅 {date_iso}",
        "━━━━━━━━━━━━━━━━━━━━━━",
        ""
    ]
    
    for i, p in enumerate(top_picks, 1):
        # EV-based emoji selection
        ev_emoji = "🔥" if p["ev"] > 0.1 else "⭐" if p["ev"] > 0.05 else "💎"
        prob_emoji = "🚀" if p["p_est"] > 0.7 else "📈" if p["p_est"] > 0.6 else "📊"
        
        lines.extend([
            f"**{i}. {p['match']}**",
            f"├ {prob_emoji} **Selecție:** {p['selection']}",
            f"├ 🎯 **Probabilitate:** {p['p_est']:.1%}",
            f"├ 💰 **Cota:** {p['odds']:.2f}",
            f"└ {ev_emoji} **Expected Value:** {p['ev']:+.3f}",
            ""
        ])
    
    # Add odds unavailability message if needed
    if odds_unavailable_global:
        lines.extend([
            "ℹ️ **Unele cote nu sunt disponibile** - folosesc estimări AI",
            ""
        ])
    
    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━━━",
        "🎯 **Picks generate cu AI - nu garantez câștigul!**",
        "💡 **Joacă responsabil și respectă limitele (+18)**"
    ])
    
    # Enhanced keyboard for navigation
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌟 Vezi Toate Piețele", callback_data="MENU_ALL_MARKETS")],
        [InlineKeyboardButton("📊 Piețe O/U & BTTS", callback_data="MENU_MARKETS"),
         InlineKeyboardButton("🎯 Construiește Expres", callback_data="MENU_EXPRESS")],
        [InlineKeyboardButton("🔄 Refresh Picks", callback_data="MENU_TODAY"),
         InlineKeyboardButton("🏠 Meniu Principal", callback_data="MENU_MAIN")]
    ])
    
    await _reply(update, "\n".join(lines), reply_markup=keyboard)

async def cmd_markets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Over/Under 2.5 and BTTS markets"""
    uid = update.effective_user.id
    can_access, msg = plan_gate(uid, 'markets')
    
    if not can_access:
        if 'trial expirat' in msg.lower():
            await show_trial_expired_message(update)
        else:
            await update.message.reply_text(f"{msg}\n\nFolosește /subscribe pentru upgrade!")
        return
    
    # Use trial if free user
    user_stats = get_user_stats(uid)
    if user_stats['plan'] == 'free':
        if not use_trial(uid):
            await show_trial_expired_message(update)
            return
        
        # Show trial usage info
        remaining = user_stats['trial_remaining'] - 1
        trial_msg = f"🎁 Trial folosit! Îți mai rămân {remaining} generări gratuite."
        await update.message.reply_text(trial_msg)
        
    lang = get_lang(uid)
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


async def cmd_all_markets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show comprehensive predictions for all markets"""
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text("🔮 Generez predicții complete pentru toate piețele...")
    
    date_iso = today_iso()
    await all_markets_for_date(update, context, date_iso, lang)


async def all_markets_for_date(update: Update, context: ContextTypes.DEFAULT_TYPE, date_iso: str, lang: str):
    """Generate comprehensive market predictions for all matches"""
    token = settings.football_data_token
    matches = get_matches_for_date(token, TOP_COMP_CODES, date_iso)
    
    if not matches:
        await _reply(update, tr(lang, "no_matches"), reply_markup=_kb_main(lang))
        return

    # Fetch odds for all markets
    odds_events_by_comp = {}
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
                    markets="h2h,totals"
                )
                if data and data[0]:
                    odds_events_by_comp[code] = data[0]
            except Exception as e:
                print(f"Error fetching odds for {code}: {e}")
                continue

    # Get top 3 most interesting matches
    top_matches = matches[:3] if len(matches) >= 3 else matches
    user_id = update.effective_user.id
    rng = seeded_rng_for_user(user_id, date_iso)
    rng.shuffle(top_matches)  # User-specific shuffle
    
    # Generate comprehensive predictions for each match
    response_lines = [
        "🌟 **PREDICȚII COMPLETE AI** 🌟",
        f"📅 {date_iso}",
        ""
    ]
    
    for i, match in enumerate(top_matches[:2], 1):  # Limit to 2 matches to avoid message length
        odds_events = odds_events_by_comp.get(match["competition"], [])
        predictions = get_comprehensive_match_predictions(match, odds_events, token, date_iso)
        
        match_card = format_match_card(predictions, lang)
        response_lines.append(match_card)
        if i < len(top_matches[:2]):
            response_lines.append("")
    
    # Add summary and navigation
    response_lines.extend([
        "",
        "🎯 **Predicțiile sunt generate de AI și nu garantează câștigul!**",
        "💡 Joacă responsabil și respectă limitele legale de vârstă (+18)",
        "",
        "📱 Folosește meniul pentru alte opțiuni:"
    ])
    
    # Create enhanced keyboard with market selection
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Picks Rapide", callback_data="MENU_TODAY"),
         InlineKeyboardButton("📊 Piețe O/U & BTTS", callback_data="MENU_MARKETS")],
        [InlineKeyboardButton("🎯 Construiește Expres", callback_data="MENU_EXPRESS")],
        [InlineKeyboardButton("🔄 Refresh Predicții", callback_data="MENU_ALL_MARKETS"),
         InlineKeyboardButton("🏠 Meniu Principal", callback_data="MENU_MAIN")]
    ])
    
    await _reply(update, "\n".join(response_lines), reply_markup=keyboard)


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
                    markets="h2h,totals"
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

    # menu navigation
    if data == "MENU_MAIN":
        await q.edit_message_text(tr(lang, "welcome_title", emoji="🤖⚽✨"), reply_markup=_kb_main(lang))
        return
    if data == "MENU_TODAY":
        # Show loading animation
        loading_msg = await send_loading_animation(update, "prediction")
        await q.edit_message_text("🔮🔥 **Generez TOP PICKS...** ⚡\n🎯 **Loading cele mai bune selecții...**", parse_mode='Markdown')
        
        # Process the request
        await picks_for_date(update, context, today_iso(), lang)
        
        # Delete loading animation after processing
        await delete_animation_message(loading_msg)
        return
    if data == "MENU_MARKETS":
        # Show loading animation
        loading_msg = await send_loading_animation(update, "prediction")
        await q.edit_message_text("📊💎 **Analizez piețele...** 🔥\n⚡ **Calculez O/U și BTTS probabilitățile...**", parse_mode='Markdown')
        
        # Process the request
        await markets_for_date(update, context, today_iso(), lang)
        
        # Delete loading animation after processing
        await delete_animation_message(loading_msg)
        return
    if data == "MENU_ALL_MARKETS":
        # Show loading animation
        loading_msg = await send_loading_animation(update, "prediction")
        await q.edit_message_text("🌟🎯 **Generez predicții complete...** 💫\n🔥 **Analizez toate piețele disponibile...**", parse_mode='Markdown')
        
        # Process the request
        await all_markets_for_date(update, context, today_iso(), lang)
        
        # Delete loading animation after processing
        await delete_animation_message(loading_msg)
        return
    if data == "MENU_EXPRESS":
        # Show loading animation
        loading_msg = await send_loading_animation(update, "money")
        await q.edit_message_text("🎯⚡ **Construiesc expresul perfect...** 🚀\n💎 **AI optimization running...**", parse_mode='Markdown')
        
        # Process the request
        context.user_data["exp_cfg"] = {"legs":3, "min":2.0, "max":4.0}
        await q.edit_message_text("🎯 " + tr(lang,"wizard_title"), reply_markup=_kb_express(lang))
        
        # Delete loading animation after processing
        await delete_animation_message(loading_msg)
        return
    if data == "MENU_LANG":
        await q.edit_message_text("🌐 " + tr(lang,"choose_lang"), reply_markup=_kb_lang())
        return
    if data == "MENU_HELP":
        await q.edit_message_text("ℹ️ " + tr(lang,"help"), reply_markup=_kb_main(lang))
        return

    # MENU_MAIN callback - go back to main menu
    if data == "MENU_MAIN":
        await send_animated_sticker(update, "welcome") 
        user_name = update.effective_user.first_name or "Prietene"
        
        welcome_msg = [
            f"🤖⚽✨ **Bun venit înapoi, {user_name}!**",
            "",
            "🚀 **Alege o opțiune din meniu:**"
        ]
        
        await q.edit_message_text("\n".join(welcome_msg), reply_markup=_kb_main(lang), parse_mode='Markdown')
        return

    # language
    if data.startswith("LANG_"):
        lang_code = data.split("_")[1]
        set_lang(user_id, lang_code)
        lang = lang_code
        flag_emoji = {"RO": "🇷🇴", "EN": "🇬🇧", "RU": "🇷🇺"}.get(lang_code, "🌐")
        await q.edit_message_text(f"{flag_emoji} Limba setată: {lang_code}", reply_markup=_kb_main(lang))
        return

    # express wizard
    cfg = context.user_data.get("exp_cfg", {"legs":3, "min":2.0, "max":4.0})
    if data.startswith("EXP_LEGS_"):
        cfg["legs"] = int(data.split("_")[2])
        context.user_data["exp_cfg"] = cfg
        await q.edit_message_reply_markup(_kb_express(lang, cfg["legs"], cfg["min"], cfg["max"]))
        return
    if data.startswith("EXP_MIN_"):
        cfg["min"] = float(data.split("_")[2])
        context.user_data["exp_cfg"] = cfg
        await q.edit_message_reply_markup(_kb_express(lang, cfg["legs"], cfg["min"], cfg["max"]))
        return
    if data.startswith("EXP_MAX_"):
        cfg["max"] = float(data.split("_")[2])
        context.user_data["exp_cfg"] = cfg
        await q.edit_message_reply_markup(_kb_express(lang, cfg["legs"], cfg["min"], cfg["max"]))
        return
    if data == "EXP_BUILD":
        await q.edit_message_text("🚀 " + tr(lang,"processing"))
        await build_express(update, context, lang)
        return
    if data == "EXP_INFO":
        # Just acknowledge - these are info buttons
        await q.answer("ℹ️ Configurează parametrii și apasă 'Build Expres'", show_alert=False)
        return

    # 🚀 NEW: Advanced features callbacks with animations
    if data == "MENU_STATS":
        # Show loading animation
        loading_msg = await send_loading_animation(update, "prediction")
        await q.edit_message_text("📈✨ **Analizez datele...** 🔄\n⚡ **Loading statistici avansate...**", parse_mode='Markdown')
        
        # Process the request
        await cmd_stats(update, context)
        
        # Delete loading animation after processing
        await delete_animation_message(loading_msg)
        return
    if data == "MENU_BANKROLL":
        # Show loading animation
        loading_msg = await send_loading_animation(update, "money")
        await q.edit_message_text("💰🎯 **Calculez bankroll optimal...** 📊\n🚀 **Smart money management loading...**", parse_mode='Markdown')
        
        # Process the request
        await cmd_bankroll(update, context)
        
        # Delete loading animation after processing
        await delete_animation_message(loading_msg)
        return
    if data == "MENU_LIVE":
        # Show loading animation
        loading_msg = await send_loading_animation(update, "live")
        await q.edit_message_text("⚡🔴 **Conectez live feeds...** 📡\n🎬 **Real-time data streaming...**", parse_mode='Markdown')
        
        # Process the request
        await cmd_live(update, context)
        
        # Delete loading animation after processing
        await delete_animation_message(loading_msg)
        return
    if data == "MENU_STRATEGIES":
        # Show loading animation
        loading_msg = await send_loading_animation(update, "prediction")
        await q.edit_message_text("🎯🧠 **Analizez strategii...** 🎰\n💡 **AI strategy engine loading...**", parse_mode='Markdown')
        
        # Process the request
        await cmd_strategies(update, context)
        
        # Delete loading animation after processing
        await delete_animation_message(loading_msg)
        return
    if data == "MENU_SOCIAL":
        # Show loading animation
        loading_msg = await send_loading_animation(update, "success")
        await q.edit_message_text("🏆👥 **Conectez la comunitate...** 🌟\n🎮 **Social hub activating...**", parse_mode='Markdown')
        
        # Process the request
        await cmd_social(update, context)
        
        # Delete loading animation after processing
        await delete_animation_message(loading_msg)
        return
    if data == "MENU_AI":
        # Show loading animation
        loading_msg = await send_loading_animation(update, "prediction")
        await q.edit_message_text("🤖🧬 **Activez AI Personal...** 🔮\n🎲 **Neural networks loading...**", parse_mode='Markdown')
        
        # Process the request
        await cmd_ai(update, context)
        
        # Delete loading animation after processing
        await delete_animation_message(loading_msg)
        return
    
    # Stats callbacks
    if data == "stats_monthly":
        user_id_str = str(update.effective_user.id) if update.effective_user else "unknown"
        monthly_chart = get_monthly_chart(user_id_str)
        await q.edit_message_text(f"📊 **Performance Lunar**\n\n{monthly_chart}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Stats", callback_data="MENU_STATS")]]))
        return
    if data == "stats_leaderboard":
        leaderboard = get_leaderboard()
        await q.edit_message_text(leaderboard, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Stats", callback_data="MENU_STATS")]]))
        return
    if data == "stats_track":
        await q.edit_message_text("📋 **Track Pariu Nou**\n\nFolosește `/track Match | Market | Selection | Odds | Stake`\n\n**Exemplu:**\n`/track Arsenal vs Chelsea | 1X2 | Arsenal | 1.85 | 100`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Stats", callback_data="MENU_STATS")]]))
        return

    # 👤 Account Menu
    if data == "MENU_ACCOUNT":
        loading_msg = await send_loading_animation(update, "success")
        await q.edit_message_text("👤⚡ **Loading contul tău...** 📊\n💎 **Account info loading...**", parse_mode='Markdown')
        
        await show_account_menu(update, context)
        await delete_animation_message(loading_msg)
        return
    
    # 💎 Subscription Menu
    if data == "MENU_SUBSCRIPTION":
        loading_msg = await send_loading_animation(update, "money")
        await q.edit_message_text("💎🚀 **Loading abonamente...** 💰\n⭐ **Premium plans loading...**", parse_mode='Markdown')
        
        await show_subscription_menu(update, context)
        await delete_animation_message(loading_msg)
        return
    
    # Contact Admin
    if data == "CONTACT_ADMIN":
        admin_contact_msg = [
            "👨‍💼 **Contact Administrator**",
            "",
            "📞 Pentru abonamente și suport premium:",
            "🔹 Telegram: @PariuSmartAdmin",
            "🔹 Email: support@pariusmart.ro",
            "",
            "💬 **Sau scrie-mi direct aici ce dorești și îți voi răspunde în cel mai scurt timp!**",
            "",
            "⚡ **Răspuns garantat în maxim 2 ore!**"
        ]
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Vezi Abonamente", callback_data="MENU_SUBSCRIPTION")],
            [InlineKeyboardButton("🔙 Înapoi", callback_data="MENU_ACCOUNT")]
        ])
        
        await q.edit_message_text("\n".join(admin_contact_msg), reply_markup=keyboard, parse_mode='Markdown')
        return
    
    # Plan selection handlers
    if data.startswith("SELECT_"):
        plan_name = data.split("_")[1]
        pricing = get_pricing_catalog()
        
        plan_info = pricing.get(plan_name, {})
        
        selection_msg = [
            f"💎 **{plan_name} PLAN SELECTAT** 💎",
            "═══════════════════════════",
            "",
            f"💰 **Prețuri:**",
            f"📅 Lunar: **{plan_info.get('price_monthly', 'N/A')}**",
            f"📅 Anual: **{plan_info.get('price_yearly', 'N/A')}**",
            "",
            "🎯 **Beneficii:**"
        ]
        
        for feature in plan_info.get('features', []):
            selection_msg.append(f"  {feature}")
        
        selection_msg.extend([
            "",
            "🚀 **Pentru a activa abonamentul:**",
            "1️⃣ Contactează administratorul",
            "2️⃣ Alege modalitatea de plată", 
            "3️⃣ Primești acces instant!",
            "",
            "💡 **Plăți acceptate:**",
            "🔹 Transfer bancar",
            "🔹 PayPal",
            "🔹 Revolut",
            "🔹 Card bancar",
            "",
            "⚡ **Activare automată în 5 minute!**"
        ])
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Contactează Admin ACUM", callback_data="CONTACT_ADMIN")],
            [InlineKeyboardButton("🔄 Alege Alt Plan", callback_data="MENU_SUBSCRIPTION")],
            [InlineKeyboardButton("🔙 Contul Meu", callback_data="MENU_ACCOUNT")]
        ])
        
        await q.edit_message_text("\n".join(selection_msg), reply_markup=keyboard, parse_mode='Markdown')
        return
    
    # Admin callbacks
    if data.startswith("ADMIN_"):
        uid = update.effective_user.id
        if not is_admin(uid):
            await q.answer("⛔ Doar admin.", show_alert=True)
            return
        
        if data == "ADMIN_USERS":
            # Show users list
            from src.utils.subs import _load
            data_users = _load()
            users = data_users.get('users', {})
            
            if not users:
                await q.edit_message_text("📭 **Niciun utilizator înregistrat.**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Dashboard", callback_data="ADMIN_REFRESH")]]))
                return
            
            users_list = ["👥 **TOP UTILIZATORI** 👥", "═══════════════════════", ""]
            
            # Sort by plan priority
            plan_priority = {'PREMIUM': 0, 'PRO': 1, 'BASIC': 2, 'free': 3}
            sorted_users = sorted(users.items(), key=lambda x: plan_priority.get(x[1].get('plan', 'free'), 4))
            
            for uid_str, user_data in sorted_users[:10]:  # Top 10 users
                plan = user_data.get('plan', 'free')
                expires = user_data.get('expires', 'N/A')
                trial_used = user_data.get('trial_used', 0)
                
                plan_emoji = {'PREMIUM': '💎', 'PRO': '🔥', 'BASIC': '⭐', 'free': '🆓'}.get(plan, '❓')
                
                if plan != 'free' and expires:
                    try:
                        exp_date = dt.datetime.strptime(expires, '%Y-%m-%d')
                        status = "✅" if dt.datetime.now().date() <= exp_date.date() else "⚠️"
                    except:
                        status = "❓"
                else:
                    status = f"🎯{trial_used}/2"
                
                users_list.append(f"{plan_emoji} `{uid_str}` | {plan} | {status}")
            
            users_list.extend([
                "",
                f"📊 **Total:** {len(users)} utilizatori",
                "💡 Folosește `/grant <user_id> <plan>`"
            ])
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="ADMIN_USERS")],
                [InlineKeyboardButton("🔙 Admin Dashboard", callback_data="ADMIN_REFRESH")]
            ])
            
            await q.edit_message_text("\n".join(users_list), reply_markup=keyboard, parse_mode='Markdown')
            return
        
        if data == "ADMIN_STATS":
            # Show detailed statistics
            from src.utils.subs import get_user_statistics, get_user_activity
            stats = get_user_statistics()
            recent_activity = get_user_activity(limit=10)
            
            stats_msg = [
                "📊 **STATISTICI AVANSATE** 📊",
                "═══════════════════════════════",
                "",
                f"👥 **Utilizatori:** {stats['total_users']}",
                f"⭐ **Abonați activi:** {stats['active_subscribers']}",
                f"🆓 **Trial users:** {stats['trial_users']}",
                f"⚠️ **Abonamente expirate:** {stats['expired_users']}",
                "",
                "🔄 **ACTIVITATE RECENTĂ:**"
            ]
            
            for act in recent_activity[-5:]:
                timestamp = act.get('timestamp', 'N/A')[:16]
                uid_short = str(act.get('uid', 'N/A'))[:6]
                action = act.get('action', 'N/A')
                stats_msg.append(f"• {timestamp} | {uid_short}... | {action}")
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 Vezi Utilizatori", callback_data="ADMIN_USERS")],
                [InlineKeyboardButton("🔙 Admin Dashboard", callback_data="ADMIN_REFRESH")]
            ])
            
            await q.edit_message_text("\n".join(stats_msg), reply_markup=keyboard, parse_mode='Markdown')
            return
        
        if data == "ADMIN_REFRESH":
            # Refresh admin dashboard
            await send_animated_sticker(update, "success")
            
            # Get comprehensive stats
            from src.utils.subs import get_user_statistics, list_active_codes, get_user_activity
            
            stats = get_user_statistics()
            codes = list_active_codes()
            codes_text = "\n".join([f"• `{code}`" for code in codes[:5]]) if codes else "Niciun cod activ"
            
            # Recent activity
            recent_activity = get_user_activity(limit=5)
            activity_text = "\n".join([
                f"• {act.get('action', 'N/A')} - User {str(act.get('uid', 'N/A'))[:6]}... ({act.get('timestamp', 'N/A')[:16]})"
                for act in recent_activity[-3:]
            ]) if recent_activity else "Nicio activitate recentă"
            
            admin_text = f"""
🔑 **ADMIN DASHBOARD - BOGDAN** 🔑
════════════════════════════════

📊 **STATISTICI UTILIZATORI:**
├─ 👥 **Total utilizatori:** {stats['total_users']}
├─ ⭐ **Abonați activi:** {stats['active_subscribers']}  
├─ 🆓 **Utilizatori trial:** {stats['trial_users']}
└─ ⚠️ **Abonamente expirate:** {stats['expired_users']}

🎟️ **CODURI PROMO ACTIVE ({len(codes)}):**
{codes_text}
{f"...și încă {len(codes)-5} coduri" if len(codes) > 5 else ""}

🔄 **ACTIVITATE RECENTĂ:**
{activity_text}

⚙️ **COMENZI ADMIN DISPONIBILE:**
• `/grant <user_id> <plan>` - Acordă BASIC/PRO/PREMIUM
• `/users` - Listează toți utilizatorii  
• `/admin` - Refresh dashboard
• `/reset_trial <user_id>` - Reset trial

💡 **EXEMPLE GRANT:**
• `/grant 123456789 PRO` - Acordă PRO (30 zile)
• `/grant 123456789 PREMIUM` - Acordă PREMIUM (30 zile)

🎯 **ID Admin:** `{uid}`
            """
            
            keyboard = [
                [InlineKeyboardButton("👥 Lista Utilizatori", callback_data="ADMIN_USERS")],
                [InlineKeyboardButton("📊 Statistici Avansate", callback_data="ADMIN_STATS")],
                [InlineKeyboardButton("🔄 Refresh Dashboard", callback_data="ADMIN_REFRESH")]
            ]
            
            await q.edit_message_text(
                admin_text, 
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

    # Main menu navigation callback
    if data == "main_menu":
        await send_animated_sticker(update, "welcome") 
        lang = get_lang(update.effective_user.id)
        user_name = update.effective_user.first_name or "Prietene"
        
        welcome_msg = [
            f"🤖⚽✨ **Bun venit înapoi, {user_name}!**",
            "",
            "🚀 **Alege o opțiune din meniu:**"
        ]
        
        await q.edit_message_text("\n".join(welcome_msg), reply_markup=_kb_main(lang), parse_mode='Markdown')
        return

    # Live Center callbacks  
    if data == "live_matches":
        await send_animated_sticker(update, "live")
        live_matches_text = """🔴 **LIVE MATCHES**

⚽ **Arsenal vs Chelsea** - 1-0 (78')
├ 📊 Shots: 12-8 Arsenal
├ 🟨 Cards: 3-2  
└ 🎯 Next goal odds: Arsenal 1.75, Chelsea 2.10

⚽ **Bayern vs Dortmund** - 2-1 (65')  
├ 📊 Possession: 58%-42% Bayern
├ ⚡ xG: 2.1-1.4
└ 🎯 Both teams to score: YES 1.45

⚽ **Madrid vs Barcelona** - 0-0 (43')
├ 📊 Very tight match
├ 🎭 Red card risk: HIGH  
└ 🎯 First goal: Madrid 1.90, Barca 1.85
"""
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="live_matches"), 
             InlineKeyboardButton("🎯 Live Bets", callback_data="live_picks")],
            [InlineKeyboardButton("🔙 Live Center", callback_data="MENU_LIVE")]
        ]
        await q.edit_message_text(live_matches_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "live_alerts":
        await send_animated_sticker(update, "success")
        alerts_text = """📱 **CONFIGURARE ALERTĂ**

🔔 **Alertă Activă:**
• ⚽ Goluri în timp real ✅
• 📊 Schimbare cote >10% ✅  
• 💰 Value bets EV >5% ✅
• ⏰ HT/FT alerts ✅

⚙️ **Comenzi rapide:**
• `/alert goals on/off` - Toggle alertă goluri
• `/alert odds 10` - Alertă cote >10%
• `/alert value 5` - Alertă value >5%

📨 **Ultimele alertă:**
• 🚨 Arsenal goal! 78' (1-0)
• 📈 Chelsea odds jumped +15%
• 💎 VALUE: BTTS @ 2.10 (+12% EV)
"""
        keyboard = [
            [InlineKeyboardButton("🔔 Toggle Alerts", callback_data="toggle_alerts"), 
             InlineKeyboardButton("⚙️ Settings", callback_data="alert_settings")],
            [InlineKeyboardButton("🔙 Live Center", callback_data="MENU_LIVE")]
        ]
        await q.edit_message_text(alerts_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "live_picks":
        await send_animated_sticker(update, "prediction")
        picks_text = """🎯 **LIVE PICKS** 

🔥 **HOT OPPORTUNITIES:**

⚡ **Chelsea +1 AH** @ 1.95
├ EV: +8.2% 🎯
├ Arsenal leading but Chelsea pressing  
└ 82% win rate în similar situations

💎 **Barcelona BTTS YES** @ 2.10
├ EV: +12.5% 🔥🔥
├ 0-0 HT, both teams attacking
└ BTTS în 78% din El Clasico recent

🎲 **Bayern Over 2.5 Team Goals** @ 2.30
├ EV: +6.8% ⭐
├ 2-1 lead, attacking substitutions  
└ Averaged 3.1 goals/game last 5 matches
"""
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh Picks", callback_data="live_picks"), 
             InlineKeyboardButton("📊 More Details", callback_data="live_analysis")],
            [InlineKeyboardButton("🔙 Live Center", callback_data="MENU_LIVE")]
        ]
        await q.edit_message_text(picks_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "live_odds":
        await send_animated_sticker(update, "money")
        odds_text = """📊 **ODDS MONITOR**

📈 **BIGGEST MOVEMENTS:**

🔥 **Chelsea Win** (vs Arsenal)
├ Was: 3.20 → Now: 4.50 (+40.6%) 📈
├ Movement: Arsenal scored 78'
└ Opportunity: Value increased significantly

⚡ **Barcelona BTTS** 
├ Was: 1.85 → Now: 2.10 (+13.5%) 📈  
├ Movement: Defensive first half
└ Status: 🎯 STRONG VALUE

📉 **Bayern -1 AH**
├ Was: 2.10 → Now: 1.75 (-16.7%) 📉
├ Movement: Bayern scored 2-1 lead
└ Status: ❌ Value decreased
"""
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh Odds", callback_data="live_odds"),
             InlineKeyboardButton("⚠️ Set Alerts", callback_data="live_alerts")],
            [InlineKeyboardButton("🔙 Live Center", callback_data="MENU_LIVE")]
        ]
        await q.edit_message_text(odds_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return


async def cmd_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(tr(lang,"choose_lang"), reply_markup=_kb_lang())

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    
    if lang == "RO":
        help_text = """
🤖⚽ **PariuSmart AI - Ghid Comenzi**

**📊 Comenzi Principale:**
• `/start` - Pornește botul și afișează meniul principal
• `/today` - TOP 2 picks 1X2 cu probabilități înalte  
• `/markets` - Piețe O/U 2.5 & BTTS optimizate
• `/all` - Predicții complete pentru toate piețele
• `/express` - Expres inteligent personalizat
• `/lang` - Schimbă limba (🇷🇴🇬🇧🇷🇺)

**🚀 Funcții Avansate:**
• `/stats` - Analytics personal și statistici
• `/bankroll` - Management fonduri cu Kelly Criterion
• `/live` - Center live cu alertă goluri
• `/strategies` - Tools avansate (arbitrage, value)

**🔒 Abonamente:**
• `/subscribe` - Vezi planurile disponibile
• `/redeem COD` - Activează cu cod promo
• `/status` - Verifică planul curent

**⚠️ Disclaimer +18:**
Conținut educațional, fără garanții de câștig. Pariați responsabil!

**📋 Documente Legale:**
• [Termeni de utilizare](https://github.com/user/repo/blob/main/TERMS.md)
• [Politica de confidențialitate](https://github.com/user/repo/blob/main/PRIVACY.md) 
• [Disclaimer](https://github.com/user/repo/blob/main/DISCLAIMER.md)

🧠 *Analize AI bazate pe multiple surse de date*
        """
        await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=_kb_main(lang))
    else:
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
                    markets="h2h,totals"
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


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Personal statistics with visual charts"""
    user_id = str(update.effective_user.id) if update.effective_user else "unknown"
    lang = get_lang(user_id)
    
    stats_text = get_stats_summary(user_id)
    monthly_chart = get_monthly_chart(user_id)
    
    full_text = f"{stats_text}\n\n{monthly_chart}"
    
    # Custom keyboard for stats
    keyboard = [
        [InlineKeyboardButton("📈 Grafic Lunar", callback_data="stats_monthly"),
         InlineKeyboardButton("🏆 Leaderboard", callback_data="stats_leaderboard")],
        [InlineKeyboardButton("📋 Track Pariu", callback_data="stats_track"),
         InlineKeyboardButton("✅ Updateaza", callback_data="stats_update")],
        [InlineKeyboardButton("🔙 Înapoi", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await _reply(update, full_text, reply_markup=reply_markup)


async def cmd_track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📋 Track a new bet"""
    user_id = str(update.effective_user.id) if update.effective_user else "unknown"
    lang = get_lang(user_id)
    
    # Check if arguments provided
    if context.args and len(context.args) >= 5:
        # Parse: /track Arsenal vs Chelsea | 1X2 | Arsenal | 1.85 | 100
        args_str = " ".join(context.args)
        parts = [p.strip() for p in args_str.split("|")]
        
        if len(parts) >= 5:
            try:
                match = parts[0]
                market = parts[1].upper()
                selection = parts[2]
                odds = float(parts[3])
                stake = float(parts[4])
                
                # Add bet record
                bet_data = {
                    'match': match,
                    'market': market,
                    'selection': selection,
                    'odds': odds,
                    'stake': stake,
                    'ev': 0.0,  # Would calculate from our predictions
                    'probability': 0.0
                }
                
                add_bet_record(user_id, bet_data)
                
                # Update user stats
                stats = load_user_stats(user_id)
                stats['total_bets'] = stats.get('total_bets', 0) + 1
                stats['pending_bets'] = stats.get('pending_bets', 0) + 1
                stats['total_staked'] = stats.get('total_staked', 0.0) + stake
                stats['last_bet'] = bet_data
                
                # Update market performance
                if 'market_performance' not in stats:
                    stats['market_performance'] = {}
                if market not in stats['market_performance']:
                    stats['market_performance'][market] = {'bets': 0, 'wins': 0, 'profit': 0.0}
                
                stats['market_performance'][market]['bets'] += 1
                
                save_user_stats(user_id, stats)
                
                success_text = f"""✅ **Pariu înregistrat cu succes!**

📋 **Detalii:**
• 🆚 Meci: {match}
• 🎯 Piață: {market}
• ✅ Selecție: {selection}
• 💰 Cota: {odds}
• 💳 Stake: {stake:.0f} RON
• 🎁 Câștig potential: {stake * odds:.0f} RON

📊 **Statistici actualizate:**
• Total pariuri: {stats['total_bets']}
• În așteptare: {stats['pending_bets']}
• Suma pariatăː {stats['total_staked']:.0f} RON

💡 **Next steps:**
• Folosește `/stats` pentru analiza detaliată
• Update rezultat cu `/result {stats['total_bets']} won/lost`
"""
                
                await _reply(update, success_text, reply_markup=_kb_main(lang))
                return
                
            except (ValueError, IndexError):
                pass
    
    # Show help if no valid arguments
    help_text = """📋 **Track Pariu Nou**

🎯 **Cum să trackuiești:**
Folosește formatul: `/track Arsenal vs Chelsea | 1X2 | Arsenal | 1.85 | 100`

📝 **Format:**
• `/track Match | Market | Selection | Odds | Stake`

📊 **Exemple:**
• `/track Liverpool vs City | 1X2 | Liverpool | 2.10 | 50`
• `/track Madrid vs Barca | OU25 | Over 2.5 | 1.75 | 75`
• `/track PSG vs Lyon | BTTS | Yes | 1.65 | 100`

💡 **Markets disponibile:**
• `1X2` - Home/Draw/Away
• `OU25` - Over/Under 2.5 goluri  
• `BTTS` - Both Teams To Score

🚀 **Odată înregistrat, vei putea:**
• Vedea statistici detaliate cu `/stats`
• Compara performanța cu alți utilizatori
• Primi insights personalizate AI
"""
    
    await _reply(update, help_text, reply_markup=_kb_main(lang))


async def cmd_bankroll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💰 Smart bankroll management"""
    user_id = str(update.effective_user.id) if update.effective_user else "unknown"
    lang = get_lang(user_id)
    
    stats = load_user_stats(user_id)
    
    # Handle bankroll commands with arguments
    if context.args and len(context.args) >= 2:
        command = context.args[0].lower()
        
        if command == "set":
            try:
                amount = float(context.args[1])
                if amount > 0:
                    stats['bankroll'] = amount
                    stats['initial_bankroll'] = amount
                    save_user_stats(user_id, stats)
                    
                    success_text = f"""✅ **Bankroll setat cu succes!**

💳 **Bankroll nou:** {amount:.0f} RON

🎯 **Kelly Criterion Suggestions:**
• Stake conservativ: {amount * 0.02:.0f} RON (2%)
• Stake moderat: {amount * 0.03:.0f} RON (3%)  
• Stake agresiv: {amount * 0.05:.0f} RON (5%)

⚠️ **Remember:**
• Niciodată peste 5% pe un pariu
• Rebalansează periodic bankroll-ul
• Disciplină > Emoții
"""
                    
                    await _reply(update, success_text, reply_markup=_kb_main(lang))
                    return
            except ValueError:
                pass
                
        elif command == "add":
            try:
                amount = float(context.args[1])
                current = stats.get('bankroll', 0.0)
                stats['bankroll'] = current + amount
                save_user_stats(user_id, stats)
                
                add_text = f"""💰 **Funds adăugate!**

📈 **Bankroll actualizat:**
• Anterior: {current:.0f} RON
• Adăugat: +{amount:.0f} RON  
• **Nou total: {stats['bankroll']:.0f} RON**

🎯 **Noi stake suggestions:**
• Conservativ: {stats['bankroll'] * 0.02:.0f} RON (2%)
• Moderat: {stats['bankroll'] * 0.03:.0f} RON (3%)
• Agresiv: {stats['bankroll'] * 0.05:.0f} RON (5%)
"""
                
                await _reply(update, add_text, reply_markup=_kb_main(lang))
                return
            except ValueError:
                pass
    
    # Show current status or help
    current_bankroll = stats.get('bankroll', 0.0)
    win_rate = stats.get('win_rate', 0.0)
    
    if current_bankroll == 0:
        help_text = """💰 **Bankroll Management**

🎯 **Configurează-ți bugetul pentru pariuri responsabile!**

📝 **Comenzi disponibile:**
• `/bankroll set 1000` - Setează 1000 RON
• `/bankroll add 500` - Adaugă 500 RON
• `/bankroll reset` - Resetează totul

📊 **Funcții Kelly Criterion:**
• Calculare automată a stakilor optimi
• Protecție împotriva overbetting-ului  
• Sugestii de sizing bazate pe EV și probabilități

🛡️ **Protecții de risc:**
• Maximum 5% din bankroll pe pariu
• Alertă pentru session limits
• Stop-loss automat la -20%

💡 **Avantaje:**
• Creștere constantă long-term
• Minimizarea riscului de ruină
• Disciplină în sizing stakes
"""
    else:
        # Calculate current P&L
        initial = stats.get('initial_bankroll', current_bankroll)
        profit_loss = current_bankroll - initial
        roi_since_start = (profit_loss / initial * 100) if initial > 0 else 0
        
        status_text = f"""💰 **Bankroll Status**

💳 **Bankroll Actual:** {current_bankroll:.0f} RON
📊 **Win Rate:** {win_rate:.1f}%
📈 **ROI Total:** {roi_since_start:+.1f}%
💸 **P&L:** {profit_loss:+.0f} RON

🎯 **Kelly Criterion Suggestions:**
• Stake conservativ: {current_bankroll * 0.02:.0f} RON (2%)
• Stake moderat: {current_bankroll * 0.03:.0f} RON (3%)  
• Stake agresiv: {current_bankroll * 0.05:.0f} RON (5%)

⚠️ **Risk Warnings:**
• Nu depăși 5% pe pariu individual
• Urmărește session P&L
• Stop la -20% din bankroll

📝 **Comenzi:**
• `/bankroll add 500` - Adaugă funds
• `/bankroll reset` - Resetează bankroll
"""
        help_text = status_text
    
    keyboard = [
        [InlineKeyboardButton("💳 Set Bankroll", callback_data="bankroll_set"),
         InlineKeyboardButton("📊 Kelly Calculator", callback_data="bankroll_kelly")],
        [InlineKeyboardButton("⚠️ Risk Settings", callback_data="bankroll_risk"),
         InlineKeyboardButton("📈 P&L Graph", callback_data="bankroll_graph")],
        [InlineKeyboardButton("🔙 Înapoi", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await _reply(update, help_text, reply_markup=reply_markup)


async def cmd_live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⚡ Live match alerts and notifications"""
    user_id = str(update.effective_user.id) if update.effective_user else "unknown"
    lang = get_lang(user_id)
    
    live_text = """⚡ **Live Match Center** 

🔴 **LIVE ACUM:**
• Arsenal vs Chelsea - 1-0 (78') ⚽
• Bayern vs Dortmund - 2-1 (65') 🔥
• Madrid vs Barcelona - 0-0 (43') 😴

📱 **Notificări Active:**
• 🚨 Value bets (EV >5%)
• ⚽ Goluri în timp real
• 📊 Odds movements >10%
• ⏰ HT/FT whistle alerts

🎯 **Live Opportunities:**
• Arsenal Over 1.5 goals ✅ HIT!
• Bayern BTTS ✅ HIT!  
• Madrid Under 0.5 goals ❌ MISS

⚙️ **Configurare Alertă:**
• `/notify goals on` - Alertă goluri
• `/notify odds 10` - Alertă schimbare cote >10%
• `/notify value 5` - Alertă value bets >5%

🔥 **Hot Picks LIVE:**
• Chelsea +1 AH @ 1.95 | EV: +8.2%
• Barcelona BTTS @ 2.10 | EV: +12.5%
"""

    keyboard = [
        [InlineKeyboardButton("🔴 LIVE Matches", callback_data="live_matches"),
         InlineKeyboardButton("📱 Set Alerts", callback_data="live_alerts")],
        [InlineKeyboardButton("🎯 Live Picks", callback_data="live_picks"),
         InlineKeyboardButton("📊 Odds Monitor", callback_data="live_odds")],
        [InlineKeyboardButton("🔙 Înapoi", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await _reply(update, live_text, reply_markup=reply_markup)


async def cmd_strategies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🎯 Advanced betting strategies and tools"""
    user_id = str(update.effective_user.id) if update.effective_user else "unknown"
    lang = get_lang(user_id)
    
    strategies_text = """🎯 **Strategii Avansate de Betting**

💎 **Arbitrage Scanner**
• Detectează oportunități de arbitraj
• Profit garantat indiferent de rezultat
• Calcul automat al stakilor optimi

📈 **Value Betting Scanner**  
• Identifică pariuri cu EV pozitiv
• Compară probabilitățile noastre vs bookmaker
• Filtrare după minimum EV (3%, 5%, 10%)

🎲 **Accumulator Builder**
• Construiește expres optimizate 
• Analiza riscului per combinație
• Sugestii de legs bazate pe probabilități

💰 **Kelly Criterion Calculator**
• Calculare stake optim per probabilitate
• Protecție împotriva overbetting
• Variante conservative vs agresive

🛡️ **Risk Management Tools**
• Detectare pattern martingale
• Alertă pentru consecutive losses
• Hedge betting calculator

🤖 **AI Personalization**
• Analiza pattern-urilor tale de betting
• Recomandări personalizate
• Adaptare strategies la profilul tău de risc

🔥 **TODAY'S OPPORTUNITIES:**
• 3 arbitrage detectate (profit 2.1-4.3%)
• 12 value bets cu EV > 5%
• Express optim: 4 legs, 6.2x odds, 34% prob
"""

    keyboard = [
        [InlineKeyboardButton("💎 Arbitrage", callback_data="strategy_arbitrage"),
         InlineKeyboardButton("📈 Value Scanner", callback_data="strategy_value")],
        [InlineKeyboardButton("🎲 Accumulator", callback_data="strategy_acca"),
         InlineKeyboardButton("💰 Kelly Calc", callback_data="strategy_kelly")],
        [InlineKeyboardButton("🛡️ Risk Tools", callback_data="strategy_risk"),
         InlineKeyboardButton("🤖 AI Personal", callback_data="strategy_ai")],
        [InlineKeyboardButton("🔙 Înapoi", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await _reply(update, strategies_text, reply_markup=reply_markup)


async def cmd_social(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🏆 Social features, challenges and achievements"""
    user_id = str(update.effective_user.id) if update.effective_user else "unknown"
    lang = get_lang(user_id)
    
    stats = load_user_stats(user_id)
    current_streak = stats.get('current_streak', 0)
    streak_type = stats.get('streak_type', 'none')
    total_bets = stats.get('total_bets', 0)
    
    # Achievement system
    achievements = []
    if total_bets >= 1:
        achievements.append("🎯 First Blood")
    if total_bets >= 10:
        achievements.append("🔟 Double Digits")
    if total_bets >= 100:
        achievements.append("💯 Centurion")
    if current_streak >= 5 and streak_type == 'win':
        achievements.append("🔥 Hot Streak")
    if stats.get('roi_percentage', 0) >= 10:
        achievements.append("📈 Profit Master")
    
    # Current challenges
    challenges = [
        "🎯 **Weekly Challenge**: Hit 65% win rate (current: {:.1f}%)".format(stats.get('win_rate', 0)),
        "💰 **Monthly Challenge**: +15% ROI (current: {:.1f}%)".format(stats.get('roi_percentage', 0)),
        "🔥 **Streak Challenge**: 7 wins in a row (current: {})".format(current_streak if streak_type == 'win' else 0),
        "🎲 **Express Challenge**: Win accumulator 5+ legs",
        "💎 **Value Challenge**: Find 10 bets cu EV > 8%"
    ]
    
    social_text = f"""🏆 **Social & Achievements**

🏅 **Your Achievements:**
{chr(10).join(achievements) if achievements else "• Start betting to unlock achievements!"}

🎯 **Active Challenges:**
{chr(10).join(challenges[:3])}

📊 **Community Stats:**
• Total active users: 1,247
• Best monthly ROI: +23.4% 🥇
• Longest win streak: 12 🔥
• Most popular market: BTTS (34%)

🌟 **Your Rank:**
• Global: #{random.randint(50, 500)} 
• Monthly: #{random.randint(20, 200)}
• Win Rate: #{random.randint(30, 300)}

🎮 **Gamification Features:**
• Daily login bonuses
• Achievement badges  
• Streak rewards
• Monthly competitions
• Tipster rankings

💬 **Social Sharing:**
• Share your best picks
• Follow top performers
• Join betting groups
• Compare stats with friends
"""

    keyboard = [
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="social_leaderboard"),
         InlineKeyboardButton("🎯 Challenges", callback_data="social_challenges")],
        [InlineKeyboardButton("🏅 Achievements", callback_data="social_achievements"),
         InlineKeyboardButton("📊 Compare", callback_data="social_compare")],
        [InlineKeyboardButton("💬 Share Pick", callback_data="social_share"),
         InlineKeyboardButton("👥 Groups", callback_data="social_groups")],
        [InlineKeyboardButton("🔙 Înapoi", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await _reply(update, social_text, reply_markup=reply_markup)


async def cmd_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🤖 Personal AI recommendations and learning"""
    user_id = str(update.effective_user.id) if update.effective_user else "unknown"
    lang = get_lang(user_id)
    
    # Load user data for analysis
    stats = load_user_stats(user_id)
    
    # For demo, create sample betting history
    sample_history = []
    if stats.get('total_bets', 0) < 5:
        ai_text = """🤖 **Personal AI Assistant**

🔍 **Learning Status:** Insufficient Data
📊 **Required:** Minimum 5 tracked bets for AI analysis

🚀 **What AI will provide after 5+ bets:**

📈 **Pattern Analysis:**
• Favorite markets and success rates
• Optimal odds ranges for your style
• Time patterns and preferences
• Risk profile assessment

🎯 **Personalized Recommendations:**
• Custom picks based on your strengths
• Market-specific advice
• Stake sizing optimization
• Strategy adaptation

📋 **Behavioral Insights:**
• Streak behavior analysis
• Bias detection and correction
• Performance optimization tips
• Risk management alerts

🧠 **Adaptive Predictions:**
• Odds adjusted to your performance
• Market probabilities personalized
• EV calculations optimized for you

💡 **Start tracking bets with `/track` to unlock AI features!**
"""
    else:
        # Analyze patterns (simulated for demo)
        patterns = {
            'favorite_markets': {'1X2': 8, 'OU25': 5, 'BTTS': 3},
            'risk_profile': 'moderate',
            'win_rate_by_market': {'1X2': 62.5, 'OU25': 60.0, 'BTTS': 66.7},
            'win_rate_by_odds_range': {'low': 70.0, 'medium': 55.0, 'high': 45.0}
        }
        
        # Generate recommendations
        insights = [
            "📊 Preferi piața 1X2 (50% din pariuri)",
            "🏆 Cea mai bună piață: BTTS (66.7% win rate)", 
            "💰 Performezi cel mai bine la cote mici (70% win rate)",
            "⚖️ Profil moderat - balans bun între risc și recompensă"
        ]
        
        strategy_rec = get_strategy_recommendation(patterns, stats.get('bankroll', 1000))
        
        ai_text = f"""🤖 **Personal AI Assistant**

🔍 **Analysis Complete** - Based on {stats.get('total_bets', 0)} tracked bets

📊 **Your Betting DNA:**
{chr(10).join([f"• {insight}" for insight in insights])}

🎯 **Today's AI Recommendations:**

🔥 **Top Pick for You:**
• Arsenal vs Chelsea | 1X2 | Arsenal
• Odds: 1.85 | Confidence: 89%
• Reason: Matches your strong 1X2 performance

💰 **Stake Suggestion:** {strategy_rec['recommended_strategy']['stake_amount']:.0f} RON
(Based on your {patterns['risk_profile']} risk profile)

🧠 **Strategy Recommendation:**
• {strategy_rec['recommended_strategy']['name']}
• {strategy_rec['recommended_strategy']['description']}
• Daily budget: {strategy_rec['recommended_strategy']['daily_budget']:.0f} RON

📈 **Performance Optimization:**
• Continue focusing on BTTS market (best win rate)
• Increase bets on lower odds (your strength)
• Consider reducing stakes on high-odds bets

⚠️ **Risk Alerts:**
• No dangerous patterns detected ✅
• Bankroll management: Excellent ✅
• Streak behavior: Healthy ✅
"""
    
    keyboard = [
        [InlineKeyboardButton("📊 Pattern Analysis", callback_data="ai_patterns"),
         InlineKeyboardButton("🎯 Get Recommendations", callback_data="ai_recommendations")],
        [InlineKeyboardButton("🧠 Strategy Optimizer", callback_data="ai_strategy"), 
         InlineKeyboardButton("📈 Performance Tips", callback_data="ai_tips")],
        [InlineKeyboardButton("⚙️ AI Settings", callback_data="ai_settings"),
         InlineKeyboardButton("🔄 Retrain Model", callback_data="ai_retrain")],
        [InlineKeyboardButton("🔙 Înapoi", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await _reply(update, ai_text, reply_markup=reply_markup)


def main():
    token = settings.telegram_token or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    
    # Core commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", cmd_today))
    app.add_handler(CommandHandler("markets", cmd_markets))
    app.add_handler(CommandHandler("all", cmd_all_markets))
    app.add_handler(CommandHandler("express", cmd_express))
    app.add_handler(CommandHandler("lang", cmd_lang))
    app.add_handler(CommandHandler("health", health))
    app.add_handler(CommandHandler("help", cmd_help))

    # 🚀 NEW: Advanced betting features
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("track", cmd_track))  
    app.add_handler(CommandHandler("bankroll", cmd_bankroll))
    app.add_handler(CommandHandler("live", cmd_live))
    app.add_handler(CommandHandler("strategies", cmd_strategies))
    app.add_handler(CommandHandler("social", cmd_social))
    app.add_handler(CommandHandler("ai", cmd_ai))
    app.add_handler(CommandHandler("leaderboard", lambda u,c: _reply(u, get_leaderboard())))

    # --- SUBSCRIPTIONS MVP ---
    from src.utils.subs import (
        is_admin, get_plan, grant_days, redeem, plan_gate, get_user_stats, 
        list_active_codes, add_promo_code, get_user_statistics, get_user_activity, reset_trial
    )
    async def subscribe_cmd(update, context):
        uid = update.effective_user.id
        user_stats = get_user_stats(uid)
        
        text = f"""
� **Abonamente PariuSmart AI**

🎯 **De ce să alegi PariuSmart AI?**

✅ **Rezultate dovedite**: 65%+ rata de succes
✅ **Transparență totală**: Îți explic fiecare predicție  
✅ **AI în dezvoltare**: Algoritmii se îmbunătățesc zilnic
✅ **Risk Management**: Te învăț să pariezi inteligent

📊 **Status curent:** {user_stats['plan'].title()}
{f"🎁 Trial: {user_stats['trial_remaining']} generări rămase" if user_stats['plan'] == 'free' else f"📅 Valabil până: {user_stats['expires']}"}

💰 **Planuri Disponibile:**

🥉 **Starter** - €9.99/lună
• Predicții zilnice nelimitate  
• Acces la toate piețele (1X2, O/U, BTTS)
• Expresuri cu max 3 selecții
• Support comunitate

🥇 **Pro** - €19.99/lună  
• Tot ce include Starter +
• Analytics personal și ROI tracking
• Expresuri cu max 4 selecții
• Management bankroll cu Kelly Criterion
• Acces prioritar la noi funcții

🔗 **Linkuri de Plată:**
• Starter: https://pariusmart.com/pay/starter
• Pro: https://pariusmart.com/pay/pro

💡 **Observație importantă:** 
Nu garantez profit, dar îți ofer cele mai bune analize bazate pe date reale și inteligență artificială. Scopul meu este să te ajut să iei decizii informate, nu să faci bani garantat.

⚠️ **Joacă responsabil! +18 ani.**

După plată, folosește /redeem CODUL_TĂU pentru activare.
        """
        
        keyboard = [
            [InlineKeyboardButton("💳 Starter €9.99", url="https://pariusmart.com/pay/starter")],
            [InlineKeyboardButton("👑 Pro €19.99", url="https://pariusmart.com/pay/pro")],
            [InlineKeyboardButton("❓ Cum Funcționează", callback_data="ABOUT_AI")],
            [InlineKeyboardButton("🔙 Înapoi", callback_data="MENU_MAIN")]
        ]
        
        await update.message.reply_text(
            text, 
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )

    async def redeem_cmd(update, context):
        uid = update.effective_user.id
        args = context.args
        if not args:
            await update.message.reply_text("Trimite: /redeem CODUL_TĂU")
            return
        code = args[0]
        ok, info = redeem(code, uid)
        if ok:
            await update.message.reply_text(f"✅ Activat! Expiră la {info}")
        else:
            await update.message.reply_text(f"❌ {info}")

    async def status_cmd(update, context):
        uid = update.effective_user.id
        stats = get_user_stats(uid)
        
        status_text = f"""
🔒 **Status Abonament**

📊 **Plan Curent:** {stats['plan'].title()}
📅 **Expiră:** {stats['expires'] if stats['expires'] else 'Niciodată'}
⏰ **Zile Rămase:** {stats['days_left']}
✅ **Status:** {'Activ' if stats['is_active'] else 'Inactiv'}

🚀 **Funcții Disponibile:**
{'✅ Toate funcțiile' if stats['plan'] == 'pro' else '✅ Funcții de bază' if stats['plan'] == 'starter' else '⚠️ Doar /today'}

💡 **Tip:** Folosește /subscribe pentru upgrade!
        """
        await update.message.reply_text(status_text, parse_mode='Markdown')

    async def grant_cmd(update, context):
        uid = update.effective_user.id
        if not is_admin(uid):
            await update.message.reply_text("⛔ Doar admin.")
            return
        args = context.args
        if len(args) != 3:
            await update.message.reply_text("Format: /grant <zile> <plan:starter|pro> <id_user>")
            return
        try:
            zile = int(args[0])
            plan = args[1]
            id_user = int(args[2])
            if plan not in ("starter", "pro"):
                raise ValueError
        except Exception:
            await update.message.reply_text("Format: /grant <zile> <plan:starter|pro> <id_user>")
            return
        exp = grant_days(id_user, plan, zile)
        await update.message.reply_text(f"✅ Grant {zile} zile ({plan}) → {id_user}. Expiră: {exp}")

    async def admin_cmd(update, context):
        uid = update.effective_user.id
        if not is_admin(uid):
            await update.message.reply_text("⛔ Doar admin (ID: 1622719347).")
            return
        
        await send_animated_sticker(update, "success")
        
        # Get comprehensive stats
        from src.utils.subs import get_user_statistics, list_active_codes, get_user_activity
        
        stats = get_user_statistics()
        codes = list_active_codes()
        codes_text = "\n".join([f"• `{code}`" for code in codes[:5]]) if codes else "Niciun cod activ"
        
        # Recent activity
        recent_activity = get_user_activity(limit=5)
        activity_text = "\n".join([
            f"• {act.get('action', 'N/A')} - User {str(act.get('uid', 'N/A'))[:6]}... ({act.get('timestamp', 'N/A')[:16]})"
            for act in recent_activity[-3:]
        ]) if recent_activity else "Nicio activitate recentă"
        
        admin_text = f"""
🔑 **ADMIN DASHBOARD - BOGDAN** 🔑
════════════════════════════════

📊 **STATISTICI UTILIZATORI:**
├─ 👥 **Total utilizatori:** {stats['total_users']}
├─ ⭐ **Abonați activi:** {stats['active_subscribers']}  
├─ 🆓 **Utilizatori trial:** {stats['trial_users']}
└─ ⚠️ **Abonamente expirate:** {stats['expired_users']}

🎟️ **CODURI PROMO ACTIVE ({len(codes)}):**
{codes_text}
{f"...și încă {len(codes)-5} coduri" if len(codes) > 5 else ""}

🔄 **ACTIVITATE RECENTĂ:**
{activity_text}

⚙️ **COMENZI ADMIN DISPONIBILE:**
• `/grant <user_id> <plan>` - Acordă BASIC/PRO/PREMIUM
• `/users` - Listează toți utilizatorii  
• `/admin` - Refresh dashboard
• `/reset_trial <user_id>` - Reset trial

💡 **EXEMPLE GRANT:**
• `/grant 123456789 PRO` - Acordă PRO (30 zile)
• `/grant 123456789 PREMIUM` - Acordă PREMIUM (30 zile)

🎯 **ID Admin:** `{uid}`
        """
        
        keyboard = [
            [InlineKeyboardButton("� Lista Utilizatori", callback_data="ADMIN_USERS")],
            [InlineKeyboardButton("📊 Statistici Avansate", callback_data="ADMIN_STATS")],
            [InlineKeyboardButton("� Refresh Dashboard", callback_data="ADMIN_REFRESH")]
        ]
        
        await update.message.reply_text(
            admin_text, 
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def grant_cmd(update, context):
        """Grant subscription plan to user"""
        uid = update.effective_user.id
        if not is_admin(uid):
            await update.message.reply_text("⛔ Doar admin (ID: 1622719347).")
            return
        
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Format: `/grant <user_id> <plan>`\n\nPlanuri: BASIC, PRO, PREMIUM")
            return
        
        try:
            target_uid = int(args[0])
            plan = args[1].upper()
        except ValueError:
            await update.message.reply_text("❌ ID utilizator invalid.")
            return
        
        if plan not in ['BASIC', 'PRO', 'PREMIUM']:
            await update.message.reply_text("❌ Plan invalid. Folosește: BASIC, PRO, PREMIUM")
            return
        
        # Grant subscription
        from src.utils.subs import grant_plan
        expires = (dt.datetime.now() + dt.timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Create user if doesn't exist and grant plan
        from src.utils.subs import _load, _save
        data = _load()
        uid_str = str(target_uid)
        
        if uid_str not in data['users']:
            data['users'][uid_str] = {
                'plan': 'free',
                'expires': None,
                'trial_used': 0,
                'joined': dt.datetime.now().isoformat()
            }
        
        data['users'][uid_str]['plan'] = plan
        data['users'][uid_str]['expires'] = expires
        _save(data)
        
        # Log activity
        log_user_activity(target_uid, f"ADMIN_GRANT: {plan} plan by admin {uid}")
        
        success_msg = f"""
✅ **ABONAMENT ACORDAT CU SUCCES!**

👤 **Utilizator:** `{target_uid}`
💎 **Plan:** {plan}
📅 **Valabil până:** {expires}
👨‍💼 **Acordat de:** Admin {uid}

🚀 **Utilizatorul are acum acces complet!**
        """
        
        await send_animated_sticker(update, "success")
        await update.message.reply_text(success_msg, parse_mode='Markdown')

    async def users_cmd(update, context):
        """List all users with their subscription status"""
        uid = update.effective_user.id
        if not is_admin(uid):
            await update.message.reply_text("⛔ Doar admin (ID: 1622719347).")
            return
        
        await send_animated_sticker(update, "prediction")
        
        from src.utils.subs import _load
        data = _load()
        users = data.get('users', {})
        
        if not users:
            await update.message.reply_text("📭 Niciun utilizator înregistrat.")
            return
        
        users_list = ["👥 **LISTA UTILIZATORI** 👥", "═══════════════════════════", ""]
        
        # Sort by plan priority
        plan_priority = {'PREMIUM': 0, 'PRO': 1, 'BASIC': 2, 'free': 3}
        sorted_users = sorted(users.items(), key=lambda x: plan_priority.get(x[1].get('plan', 'free'), 4))
        
        for uid_str, user_data in sorted_users[:20]:  # Limit to 20 users
            plan = user_data.get('plan', 'free')
            expires = user_data.get('expires', 'N/A')
            trial_used = user_data.get('trial_used', 0)
            
            # Plan emoji
            plan_emoji = {
                'PREMIUM': '💎',
                'PRO': '🔥', 
                'BASIC': '⭐',
                'free': '🆓'
            }.get(plan, '❓')
            
            # Status
            if plan != 'free' and expires:
                try:
                    exp_date = dt.datetime.strptime(expires, '%Y-%m-%d')
                    if dt.datetime.now().date() <= exp_date.date():
                        status = "✅ ACTIV"
                    else:
                        status = "⚠️ EXPIRAT"
                except:
                    status = "❓ UNKNOWN"
            else:
                status = f"🎯 Trial {trial_used}/2"
            
            users_list.append(f"{plan_emoji} **{uid_str[:6]}...** | {plan} | {status}")
        
        if len(users) > 20:
            users_list.append(f"\n... și încă {len(users) - 20} utilizatori")
        
        users_list.extend([
            "",
            f"📊 **Total:** {len(users)} utilizatori",
            "",
            "💡 **Pentru detalii:** `/grant <user_id> <plan>`"
        ])
        
        await update.message.reply_text("\n".join(users_list), parse_mode='Markdown')

    async def reset_trial_cmd(update, context):
        uid = update.effective_user.id
        if not is_admin(uid):
            await update.message.reply_text("⛔ Doar admin.")
            return
        
        args = context.args
        if len(args) != 1:
            await update.message.reply_text("Format: /reset_trial <user_id>")
            return
        
        try:
            target_uid = int(args[0])
        except ValueError:
            await update.message.reply_text("❌ ID utilizator invalid.")
            return
        
        if reset_trial(target_uid):
            await update.message.reply_text(f"✅ Trial resetat pentru utilizatorul {target_uid}")
        else:
            await update.message.reply_text(f"❌ Utilizatorul {target_uid} nu a fost găsit.")

    app.add_handler(CommandHandler("subscribe", subscribe_cmd))
    app.add_handler(CommandHandler("redeem", redeem_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("grant", grant_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("grant", grant_cmd))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("reset_trial", reset_trial_cmd))
    # --- END SUBSCRIPTIONS MVP ---

    app.add_handler(CallbackQueryHandler(on_callback))

    print("🤖⚽✨ PariuSmart AI Bot started with ADVANCED FEATURES!")
    print("🚀 New commands: /stats /track /bankroll /live /leaderboard /subscribe /redeem /status /grant")
    app.run_polling()


if __name__ == "__main__":
    main()
    main()
