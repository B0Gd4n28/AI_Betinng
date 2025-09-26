LANGS = ["RO","EN","RU"]

T = {
  "RO": {
    "app_name": "PariuSmart AI",
    "app_name_emoji": "🤖⚽️✨",
    "welcome_title": "Bun venit la PariuSmart AI {emoji}",
    "welcome_features": (
      "🎯 **Ce pot face pentru tine:**\n"
      "├ � **Picks zilnice** - Top selecții AI cu probabilități mari\n"
      "├ � **Piețe multiple** - O/U 2.5, BTTS cu analiza avansată\n" 
      "├ � **Predicții complete** - Toate piețele pentru meciuri\n"
      "└ 🎯 **Expresuri inteligente** - Optimizate automat pentru profit"
    ),
    "welcome_commands": (
      "🧠 **Powered by:**\n"
      "• Machine Learning cu învățare continuă\n"
      "• Analiza weather, sentiment și statistici live\n"
      "• Expected Value (EV) calculation pentru fiecare pick"
    ),
    "welcome_disclaimer": "⚠️ **Important:** Joacă responsabil! +18 ani, respectă legislația locală",
    "start": "Salut! 👋 Alege o acțiune:",
    "menu_picks": "Picks Azi",
    "menu_markets": "Piețe (O/U & BTTS)", 
    "menu_express": "Expres",
    "menu_lang": "Limba",
    "menu_help": "Ajutor",
    "help": (
      "🤖 **PariuSmart AI** - Agent inteligent pentru pariuri\n\n"
      "🔥 **Comenzi disponibile:**\n"
      "• `/today` — cele mai bune 2 selecții 1X2 pentru azi\n"
      "• `/markets` — piețe Over/Under 2.5 & Both Teams To Score\n"
      "• `/all` — predicții complete pentru toate piețele\n"
      "• `/express [min] [max] [legs]` — expres rapid optimizat\n"
      "• `/health` — verifică statusul tuturor API-urilor\n"
      "• `/lang` — schimbă limba (RO/EN/RU)\n\n"
      "🎯 **Poți folosi și butoanele din meniul principal!**\n\n"
      "💡 **Toate predicțiile combină:**\n"
      "├ Analiza formei echipelor\n"
      "├ Cotele live de la bookmaker-i\n"
      "├ Algoritmi AI cu învățare continuă\n"
      "├ Condiții meteo și sentiment analysis\n"
      "└ Expected Value (EV) calculation\n\n"
      "🏆 **Pentru rezultate optime, verifică predicțiile zilnic!**"
    ),
    "choose_lang": "🌐 Alege limba preferată:",
    "lang_label_ro": "🇷🇴 Română",
    "lang_label_en": "🇬🇧 English", 
    "lang_label_ru": "🇷🇺 Русский",
    "lang_set": "✅ Limba a fost setată: {language}",
    "processing": "🔮 Procesez cu AI... te rog așteaptă 2-3 secunde ⏳",
    "no_matches": "❌ Nu am găsit meciuri pentru azi în ligile monitorizate.",
    "today_header": "� TOP PICKS AI pentru {date}",
    "today_top2": "🎯 Cele mai bune 2 selecții personalizate pentru tine:",
    "markets_header": "📊 PIEȚE SPECIALE pentru {date}",
    "express_header": "🎯 EXPRES AI ({legs} selecții) pentru {date}",
    "express_fail": "Nu am reușit să compun un expres în parametrii dați.",
    "express_combined": "Prob combinată≈{prob:.3f} | Cote totale {odds:.2f} | EV {ev:.3f}",
    "match_insights": "🧠 Insights meci",
    "health_title": "🏥 Status Sistem",
    "health": (
      "Status API-uri:\n"
      "• Football-Data: {fd}\n"
      "• The Odds API: {odds}\n"
      "• API-Football: {api_football}\n"
      "• OpenWeather: {weather}\n"
      "• Reddit: {reddit}\n"
      "• Video API: {video}\n"
      "• GDELT: {gdelt}"
    ),
    "wizard_title": "Configurează expresul:",
    "legs": "Selecții",
    "min_odds": "Cote min",
    "max_odds": "Cote max",
    "build": "Construiește",
    "odds_unavailable": "ℹ️ Cotele indisponibile pe planul gratuit; am folosit doar forma echipelor.",
    "info_fallback": "ℹ️ Unele cote pot fi indisponibile — am folosit analiza formei echipelor.",
    "disclaimer": "⚠️ Pariurile implică risc. +18. Nu există garanții. Joacă responsabil."
  },
  "EN": {
    "app_name": "PariuSmart AI",
    "app_name_emoji": "🤖⚽️✨",
    "welcome_title": "Welcome to PariuSmart AI {emoji}",
    "welcome_body": (
      "🎯 Smart sports betting agent\n\n"
      "What it offers:\n"
      "• 📊 Advanced AI analysis with multiple markets\n"
      "• 🎯 Auto-optimized parlays\n"
      "• 📈 Predictions based on form, odds & stats\n"
      "• 🌤️ Weather conditions for matches\n"
      "• 🗣️ Public sentiment analysis\n"
      "• 🌐 Multilingual support (RO/EN/RU)\n\n"
      "Quick commands:\n"
      "• /today — top 2 1X2 picks today\n"
      "• /markets — O/U 2.5 & BTTS markets\n"
      "• /express — custom parlays\n"
      "• /health — API status check"
    ),
    "welcome_disclaimer": "🔞 Disclaimer: 18+ only. Betting involves risks. Play responsibly!",
    "start": "Hi! 👋 Choose an action:",
    "menu_picks": "🔎 Today's picks",
    "menu_markets": "📊 Markets (O/U & BTTS)",
    "menu_express": "🎯 Parlay",
    "menu_lang": "🌐 Language",
    "menu_help": "ℹ️ Help",
    "help": (
      "🤖 PariuSmart AI - Smart betting agent\n\n"
      "Available commands:\n"
      "• /today — best 2 1X2 selections for today\n"
      "• /markets — Over/Under 2.5 & Both Teams To Score markets\n"
      "• /express [min] [max] [legs] — quick parlay\n"
      "• /health — check API status\n"
      "• /lang — change language\n\n"
      "You can also use the main menu buttons.\n\n"
      "💡 All predictions combine team form analysis with bookmaker odds and AI algorithms."
    ),
    "choose_lang": "Choose language:",
    "lang_label_ro": "🇷🇴 Română",
    "lang_label_en": "🇬🇧 English",
    "lang_label_ru": "🇷🇺 Русский",
    "lang_set": "Language set to: {language}",
    "processing": "Working... please wait 2–3 seconds ⏳",
    "no_matches": "No matches found for today.",
    "today_header": "📅 {date} — TOP 2 (1X2)",
    "today_top2": "🎯 Top 2 selections personalized for you:",
    "markets_header": "📊 {date} — O/U 2.5 & BTTS",
    "express_header": "🎯 {date} — Parlay ({legs} selections)",
    "express_fail": "Couldn't build a parlay for the given parameters.",
    "express_combined": "Combined Prob≈{prob:.3f} | Total Odds {odds:.2f} | EV {ev:.3f}",
    "match_insights": "🧠 Match insights",
    "health_title": "🏥 System Status",
    "health": (
      "API Status:\n"
      "• Football-Data: {fd}\n"
      "• The Odds API: {odds}\n"
      "• API-Football: {api_football}\n"
      "• OpenWeather: {weather}\n"
      "• Reddit: {reddit}\n"
      "• Video API: {video}\n"
      "• GDELT: {gdelt}"
    ),
    "wizard_title": "Configure parlay:",
    "legs": "Legs",
    "min_odds": "Min odds",
    "max_odds": "Max odds",
    "build": "Build",
    "odds_unavailable": "ℹ️ Odds unavailable on free plan; used team form only.",
    "info_fallback": "ℹ️ Some odds may be unavailable — used team form analysis.",
    "disclaimer": "⚠️ Betting involves risk. 18+. No guarantees. Play responsibly."
  },
  "RU": {
    "app_name": "PariuSmart AI",
    "app_name_emoji": "🤖⚽️✨",
    "welcome_title": "Добро пожаловать в PariuSmart AI {emoji}",
    "welcome_body": (
      "🎯 Умный агент для спортивных ставок\n\n"
      "Что предлагает:\n"
      "• 📊 Продвинутый ИИ-анализ с множественными рынками\n"
      "• 🎯 Авто-оптимизированные экспрессы\n"
      "• 📈 Прогнозы на основе формы, коэффициентов и статистики\n"
      "• �️ Погодные условия для матчей\n"
      "• 🗣️ Анализ общественных настроений\n"
      "• �🌐 Мультиязычность (RO/EN/RU)\n\n"
      "Быстрые команды:\n"
      "• /today — топ 2 пика 1X2 на сегодня\n"
      "• /markets — рынки ТБ/ТМ 2.5 и ОЗ\n"
      "• /express — настраиваемые экспрессы\n"
      "• /health — проверка статуса API"
    ),
    "welcome_disclaimer": "🔞 Дисклеймер: Только 18+. Ставки связаны с рисками. Играйте ответственно!",
    "start": "Привет! 👋 Выбери действие:",
    "menu_picks": "🔎 Пики на сегодня",
    "menu_markets": "📊 Рынки (ТБ/ТМ & ОЗ)",
    "menu_express": "🎯 Экспресс",
    "menu_lang": "🌐 Язык",
    "menu_help": "ℹ️ Помощь",
    "help": (
      "🤖 PariuSmart AI - Умный агент для ставок\n\n"
      "Доступные команды:\n"
      "• /today — лучшие 2 варианта 1X2 на сегодня\n"
      "• /markets — рынки Тотал Больше/Меньше 2.5 и Обе забьют\n"
      "• /express [min] [max] [legs] — быстрый экспресс\n"
      "• /health — проверить статус API\n"
      "• /lang — сменить язык\n\n"
      "Можно также использовать кнопки главного меню.\n\n"
      "💡 Все прогнозы сочетают анализ формы команд с коэффициентами букмекеров и ИИ-алгоритмами."
    ),
    "choose_lang": "Выберите язык:",
    "lang_label_ro": "🇷🇴 Română",
    "lang_label_en": "🇬🇧 English",
    "lang_label_ru": "🇷🇺 Русский",
    "lang_set": "Язык установлен: {language}",
    "processing": "Обрабатываю... подождите 2–3 сек ⏳",
    "no_matches": "На сегодня матчи не найдены.",
    "today_header": "📅 {date} — ТОП 2 (1X2)",
    "today_top2": "🎯 Топ 2 варианта, персонализированные для вас:",
    "markets_header": "📊 {date} — ТБ/ТМ 2.5 & ОЗ",
    "express_header": "🎯 {date} — Экспресс ({legs} ставок)",
    "express_fail": "Не получилось собрать экспресс с заданными параметрами.",
    "express_combined": "Общая Вер≈{prob:.3f} | Итого Коэф {odds:.2f} | EV {ev:.3f}",
    "match_insights": "🧠 Инсайты матча",
    "health_title": "🏥 Состояние Системы",
    "health": (
      "Статус API:\n"
      "• Football-Data: {fd}\n"
      "• The Odds API: {odds}\n"
      "• API-Football: {api_football}\n"
      "• OpenWeather: {weather}\n"
      "• Reddit: {reddit}\n"
      "• Video API: {video}\n"
      "• GDELT: {gdelt}"
    ),
    "wizard_title": "Настройка экспресса:",
    "legs": "Ставок",
    "min_odds": "Мин коэф.",
    "max_odds": "Макс коэф.",
    "build": "Собрать",
    "odds_unavailable": "ℹ️ Коэффициенты недоступны на бесплатном тарифе; использована только форма команд.",
    "info_fallback": "ℹ️ Некоторые коэффициенты могут быть недоступны — использован анализ формы команд.",
    "disclaimer": "⚠️ Азартные игры несут риск. 18+. Гарантий нет. Играйте ответственно."
  }
}

def tr(lang:str, key:str, **kwargs) -> str:
    l = lang if lang in T else "RO"
    s = T[l].get(key, key)
    return s.format(**kwargs) if kwargs else s