# FREE Soccer Picks Telegram Bot (MVP)

MVP **gratuit** care folosește:
- **Football-Data.org** (fixtures, echipe, meciuri de azi, formă din meciurile anterioare) — planul **Free** e pe veci (cu rate limit).  
- **The Odds API** (cote *H2H* pre-meci) — plan **Free** cu ~500 calls/lună, suficient pentru MVP.  
- (opțional) **GDELT DOC 2.0** pentru un scor simplu de *news/sentiment* pe ultimele 24–72h (poți porni mai târziu).

> ⚠️ Pariurile implică risc ridicat. Nu promitem profit. Respectă legislația și include mesaje de joc responsabil (+18).

## Rapid Start

1. **Chei API** (exportă în env):
   ```bash
   export FOOTBALL_DATA_TOKEN="fd_xxx"      # https://www.football-data.org/  (Free forever)
   export ODDS_API_KEY="odds_xxx"           # https://the-odds-api.com/ (Free ~500 calls/lună)
   # opțional (nu e necesar pentru MVP):
   export GDELT_ENABLED="0"
   ```

2. **Instalare**:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Rulează botul Telegram**:
   ```bash
   export TELEGRAM_BOT_TOKEN="123456:ABC..."
   python bot/bot.py
   ```

## Comenzi Bot
- `/today` → cele mai bune **picks** pentru **azi** (top 10 ligi + cupe populare configurate).
- `/express [min_odds] [max_odds] [legs]` → compune un **expres high-prob** în intervalul de cote dorit (ex. `/express 2 4 3`).  
- `/health` → status API & rate limits.

## Cum estimează probabilități
1) **Din cote** (The Odds API) → probabilități implicite (scoaterea marjei, consens pe mai mulți bookmakeri).  
2) Dacă lipsesc cote pentru un meci: **formă echipe** din ultimele 5 jocuri (puncte 3/1/0) → mapping logistic simplu.  
3) Îmbinare: dacă avem și cote, și formă, facem un **blend**: `p = 0.8*p_from_odds + 0.2*p_from_form`.

## Ligi/competiții incluse (config implicit)
- **PL (Anglia), PD (La Liga), SA (Serie A), BL1 (Bundesliga), FL1 (Ligue 1), DED (Eredivisie), PPL (Primeira Liga)**,  
- **CL (UCL), EL (UEL), UCL (UEFA Conference League)** — coduri conform Football-Data. Le poți ajusta în `src/utils/leagues.py`.

## Limitări & Note
- Football-Data Free: ~10 req/min (înregistrat) + acoperire clar listată; vezi pagina Coverage.  
- The Odds API Free: cote limitate; când quota se termină, botul trece pe formă-only.
- GDELT: gratuit; îl poți porni ulterior pentru scor de „buzz”.

Succes! 🚀

---

## Proiect A→Z (plan pentru varianta gratuită → scalare)

### 1) **Ingestion (gratuit)**
- Football-Data.org (fixtures de azi, istorice scurte pentru formă).
- The Odds API (cote H2H; la epuizare quota → fallback formă).
- (opțional) GDELT pentru scor de știri/sentiment.

### 2) **Feature Engineering**
- Probabilități implicite din cote (scoatere marjă, consens multi-book).
- Formă: puncte din ultimele 5 meciuri, golaveraj recent (extensibil).
- (ulterior) absențe/lineups, xG, news/sentiment.

### 3) **Modelul AI (agent)**
- Inițial: blend {cote 80% + formă 20%}.
- Training offline lunar/săptămânal pe CSV istoric → LogisticRegression calibrat (isotonic).
- Export model `.joblib`, servit în `ForecastAgent` (vezi `src/ai/agent.py`).

### 4) **Generare Picks & Expres**
- Selectezi per meci outcome cu `p` maxim (Home/Draw/Away).
- Expres high-prob: greedy până la cote totale target (2–4) și `legs` 2–4; optimizezi probabilitatea combinată.

### 5) **UI/UX Telegram (multilingv)**
- Meniu principal cu **butoane**: Picks azi / Expres / Limba / Help.
- Wizard pentru Expres: alege `legs`, `min_odds`, `max_odds` din butoane → “Construiește”.
- Suport limbi: **Română, English, Русский** (comutare din UI).

### 6) **Deploy & Observabilitate**
- Rulezi ca serviciu (pm2/systemd) + `.env` pentru chei.
- Logging simplu (stdout → file) + rate-limit handling pentru API-uri.
- Caching local 1–5 minute pentru a reduce call-urile.

### 7) **Scalare (ulterior)**
- DB (Postgres) + joburi periodice (cron) pentru dataset istoric.
- Dashboard (FastAPI) cu picks/expres + abonamente (Stripe).
- Adaugi surse bogate (lineups/injuries, Betfair, xG) și un pipeline de ML stabil.

**Disclaimer**: produsul nu garantează profit. Respectă legislația și bunele practici de joc responsabil.

## Configurare prin `.env`
1) Copiază `.env.example` în `.env` și completează cheile:
   ```bash
   cp .env.example .env
   # editează valorile:
   # TELEGRAM_BOT_TOKEN=...
   # FOOTBALL_DATA_TOKEN=...
   # ODDS_API_KEY=...
   ```
2) Botul încarcă `.env` automat (python-dotenv). Poți rula direct:
   ```bash
   python bot/bot.py
   ```
