# Copilot Instructions for PariuSmart AI Bot

## Project Overview
PariuSmart AI is a modular Telegram bot for advanced football betting analytics. It combines data fetchers, analytics, AI/ML, and interactive Telegram features. The codebase is designed for extensibility, resilience, and multi-language support.

## Key Architecture
- **bot/bot.py**: Main entrypoint, command handlers, menu logic, reply helpers. All new bot features and commands should be registered here.
- **src/fetchers/**: Data sources (football_data, odds_api, etc). Each fetcher implements caching and graceful error handling.
- **src/analytics/**: Market logic, probability blending, express builder, stats, strategies. Use these for all betting calculations.
- **src/utils/**: Config, i18n, storage, subscriptions, caching. Centralized config and utility functions.
- **data/**: Persistent storage (subscriptions.json, user stats, etc). Always check for file existence and create if missing.
- **assets/**: Animations, stickers, and media for bot UI.

## Developer Workflows
- **Local run**: `python -m bot.bot` (preferred) or `python bot/bot.py`
- **Windows deployment**: Use PowerShell scripts in `deploy/` for Task Scheduler integration. See README for details.
- **Linux deployment**: Use systemd service or NSSM for background running.
- **Testing**: Manual command invocation in Telegram. No automated test suite yet.
- **Debugging**: Check `logs/bot.log` for runtime errors and analytics.

## Project Conventions
- **Graceful degradation**: All features must handle missing files, API errors, and rate limits without crashing. Use try/except and fallback logic.
- **No secrets in logs/messages**: Never print or log API keys, tokens, or sensitive data.
- **Multi-language**: Use `src/i18n.py` for all user-facing text. Default is RO, but support EN/RU.
- **Animated UI**: Use emoji/sticker sequences for feedback and status. See `send_loading_animation`, `send_animated_sticker` in `bot.py`.
- **Command registration**: All new commands must be added via `app.add_handler(CommandHandler(...))` in `main()`.
- **Subscription logic**: Use `src/utils/subs.py` for all plan checks, grants, and code redemption. Always check for file existence before reading/writing.
- **Feature gating**: Use `plan_gate(uid, feature)` to restrict access based on subscription plan.

## Integration Points
- **External APIs**: football-data.org, the-odds-api.com, api-sports.io, openweather, Reddit, GDELT. All keys in `.env`, never hardcoded.
- **Payment links**: For MVP, use placeholder links in `/subscribe`. No webhook integration yet.
- **Legal docs**: TERMS.md, PRIVACY.md, DISCLAIMER.md in repo root. Link these in `/help` and README.

## Examples
- To add a new command:
  1. Implement async handler in `bot.py`
  2. Register with `app.add_handler(CommandHandler("yourcmd", yourcmd_handler))`
  3. Use `_reply(update, text)` for responses
- To add a new feature with plan restriction:
  1. Use `plan_gate(uid, "feature")` before executing logic
  2. Respond with error if not permitted

## References
- See `README.md` for deployment, architecture, and command documentation.
- See `src/utils/subs.py` for subscription logic and examples.
- See `bot/bot.py` for command patterns and UI conventions.

---
If any section is unclear or missing, please provide feedback for improvement.
