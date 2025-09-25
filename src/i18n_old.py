
LANGS = ["RO","EN","RU"]

T = {
  "RO": {
    "app_name": "Picks & Expresuri (MVP)",
    "start": "Salut! 👋 Alege o acțiune:",
    "menu_picks": "🔎 Picks azi",
    "menu_express": "🎯 Expres",
    "menu_lang": "🌐 Limba",
    "menu_help": "ℹ️ Ajutor",
    "help": (
      "Comenzi:\n"
      "• /today — cele mai bune selecții pentru azi\n"
      "• /express [min] [max] [legs] — expres rapid\n"
      "• /lang — schimbă limba\n\n"
      "Poți folosi și butoanele din meniu."
    ),
    "choose_lang": "Alege limba:",
    "lang_set": "Limba a fost setată: {lang}",
    "processing": "Procesez... te rog așteaptă 2-3 secunde ⏳",
    "no_matches": "Nu am găsit meciuri pentru azi.",
    "today_header": "📅 {date} — TOP picks ({n} selecții):",
    "express_header": "📅 {date} — Expres propus:",
    "express_fail": "Nu am reușit să compun un expres în parametrii dați.",
    "health": "Football-Data: {fd}\nThe Odds API: {odds}\nGDELT: {gdelt}",
    "wizard_title": "Configurează expresul:",
    "legs": "Selecții",
    "min_odds": "Cote min",
    "max_odds": "Cote max",
    "build": "Construiește",
    "disclaimer": "⚠️ Pariurile implică risc. +18. Nu există garanții. Joacă responsabil."
  },
  "EN": {
    "app_name": "Picks & Parlays (MVP)",
    "start": "Hi! 👋 Choose an action:",
    "menu_picks": "🔎 Today’s picks",
    "menu_express": "🎯 Parlay",
    "menu_lang": "🌐 Language",
    "menu_help": "ℹ️ Help",
    "help": (
      "Commands:\n"
      "• /today — best picks for today\n"
      "• /express [min] [max] [legs] — quick parlay\n"
      "• /lang — change language\n\n"
      "You can also use the menu buttons."
    ),
    "choose_lang": "Choose language:",
    "lang_set": "Language set to: {lang}",
    "processing": "Working... please wait 2–3 seconds ⏳",
    "no_matches": "No matches found for today.",
    "today_header": "📅 {date} — TOP picks ({n} selections):",
    "express_header": "📅 {date} — Suggested parlay:",
    "express_fail": "Couldn't build a parlay for the given parameters.",
    "health": "Football-Data: {fd}\nThe Odds API: {odds}\nGDELT: {gdelt}",
    "wizard_title": "Configure parlay:",
    "legs": "Legs",
    "min_odds": "Min odds",
    "max_odds": "Max odds",
    "build": "Build",
    "disclaimer": "⚠️ Betting involves risk. 18+. No guarantees. Play responsibly."
  },
  "RU": {
    "app_name": "Пики и Экспрессы (MVP)",
    "start": "Привет! 👋 Выбери действие:",
    "menu_picks": "🔎 Пики на сегодня",
    "menu_express": "🎯 Экспресс",
    "menu_lang": "🌐 Язык",
    "menu_help": "ℹ️ Помощь",
    "help": (
      "Команды:\n"
      "• /today — лучшие варианты на сегодня\n"
      "• /express [min] [max] [legs] — быстрый экспресс\n"
      "• /lang — сменить язык\n\n"
      "Можно также использовать кнопки меню."
    ),
    "choose_lang": "Выберите язык:",
    "lang_set": "Язык установлен: {lang}",
    "processing": "Обрабатываю... подождите 2–3 сек ⏳",
    "no_matches": "На сегодня матчи не найдены.",
    "today_header": "📅 {date} — ТОП пикы ({n} вариантов):",
    "express_header": "📅 {date} — Рекомендуемый экспресс:",
    "express_fail": "Не получилось собрать экспресс с заданными параметрами.",
    "health": "Football-Data: {fd}\nThe Odds API: {odds}\nGDELT: {gdelt}",
    "wizard_title": "Настройка экспресса:",
    "legs": "Ставок",
    "min_odds": "Мин коэф.",
    "max_odds": "Макс коэф.",
    "build": "Собрать",
    "disclaimer": "⚠️ Азартные игры несут риск. 18+. Гарантий нет. Играйте ответственно."
  }
}

def tr(lang:str, key:str, **kwargs) -> str:
    l = lang if lang in T else "RO"
    s = T[l].get(key, key)
    return s.format(**kwargs) if kwargs else s
