# PariuSmart AI - Advanced Sports Betting Bot

🤖⚽️✨ **Agent inteligent pentru pariuri sportiv## 📱 Comenzi Bot

### Comenzi Principale
- `/start` → Mesaj de bun venit cu interfață modernă și animație
- `/today` → **TOP 2 picks 1X2** personalizate cu EV calculation  
- `/markets` → **Piețe O/U 2.5 & BTTS** cu procente mari
- `/all` → **🌟 PREDICȚII COMPLETE** pentru toate piețele (nou!)
- `/express [min] [max] [legs]` → **Expresuri rapide** optimizate AI
- `/health` → **Status toate API-urile** (OK/MISSING, fără a afișa chei)
- `/lang` → **Comută limba** cu steaguri (🇷🇴🇬🇧🇷🇺)

### 🚀 NEW: Advanced Features (Surprise!) - NOW WITH ANIMATIONS! 🎬
- `/stats` → **📊 Personal Analytics** cu grafice vizuale, ROI, streaks + **animații live**
- `/track` → **📋 Track Pariuri** pentru statistici personale cu **efecte vizuale** 
- `/bankroll` → **💰 Kelly Criterion** management cu protecții risc + **animații money**
- `/live` → **⚡ Live Center** cu alertă goluri și schimbări cote + **live animations**
- `/strategies` → **🎯 Advanced Tools** (arbitrage, value scanner, accumulator) + **prediction effects**
- `/social` → **🏆 Challenges & Achievements** cu leaderboards și gamification + **success animations**
- `/ai` → **🤖 Personal AI** cu recomandări bazate pe pattern-urile tale + **neural animations**
- `/leaderboard` → **🥇 Top Performeri** cu ROI și win rates

#### 🎬 **ANIMAȚII & EFECTE VIZUALE** (NEW!)
- **🎯 Animated Stickers** similare cu https://t.me/addstickers/NewsEmoji pentru fiecare acțiune
- **⚡ Loading Animations** pentru predicții, live center, stats cu progres bars
- **🔥 Visual Confidence** sistem cu emoji-uri dinamice bazate pe probabilități
- **💎 Success Celebrations** animații pentru picks de succes și achievements
- **🎊 Welcome Animation** sequence la `/start` cu efecte spektaculoase
- **🎯 Target Indicators** pentru cele mai bune picks în fiecare piață

### Meniu Interactiv Modern
- 🔥 **Picks Azi** → Cele mai bune 2 selecții 1X2 cu probabilități
- 📊 **Piețe (O/U & BTTS)** → 3-4 picks mixte cu EV pozitiv  
- 🎯 **Predicții Complete** → Match cards cu toate piețele (nou!)
- 🎯 **Expres** → Wizard configurabil cu setări vizuale

#### 🚀 Advanced Menu (Surpriză Maximă!) - **CU ANIMAȚII LIVE! 🎬**
- 📈 **Stats & Analytics** → Dashboard personal cu grafice și metrici + **🎯 prediction animations**
- 💰 **Bankroll** → Management inteligent cu Kelly Criterion și protecții + **💎 money effects**  
- ⚡ **Live Center** → Matches live, alertă instant, odds monitoring + **⚡ live streaming effects**
- 🎯 **Strategies** → Arbitrage scanner, value bets, accumulator builder + **🔥 strategy animations**
- 🏆 **Social & Challenges** → Achievements, streaks, competiții, leaderboards + **🎊 success celebrations**
- 🤖 **Personal AI** → Analiza pattern-urilor + recomandări personalizate + **🧬 neural animations**

### 🎬 **ANIMAȚII ȘI EFECTE VIZUALE PREMIUM**
- **Telegram-style Animated Stickers** pentru fiecare funcție
- **Live Loading Effects** cu progress bars și visual feedback
- **Dynamic Confidence Indicators**: 🔥🔥🔥 (High), 🔥🔥 (Medium), 🔥 (Standard) 
- **Target Highlighting**: 🎯 pentru best picks în fiecare piață
- **Celebration Animations**: 🎊💎🔥 pentru successe și achievements
- **Welcome Animation Sequence** la startup cu efecte progressive
- **Navigation Animations** pentru toate butoanele și meniuri

- 🌐 **Limba** → Română/English/Русский cu steaguri 
- ℹ️ **Ajutor** → Ghid complet comenzi cu explicații AImulti-sursă și predicții avansate.

## ✨ Funcționalități Principale

### 🎯 **Piețe Multiple**
- **1X2** (Home/Draw/Away) - piața clasică  
- **Over/Under 2.5** - totalul golurilor
- **Both Teams To Score (BTTS)** - ambele echipe marchează
- Calculare automată **Expected Value (EV)** pentru fiecare pick

### 🧠 **Analiza AI Avansată**
- **Probabilități implicite** din cote (normalizare fără marjă, consens multi-bookmaker)
- **Formă echipe** din ultimele 5 meciuri (puncte 3/1/0)
- **Statistici echipe** (goluri medii, cartonașe, formația de acasă/deplasare)
- **Condiții meteo** pentru meciuri (temperatură, vânt, probabilitate ploaie)
- **Analiza sentimentului** din Reddit și știri internaționale (GDELT)
- **Sistem de blend** cu modele ML locale (învățare continuă)

### 🎯 **Expresuri Inteligente**
- **Diversificare per utilizator** (fiecare user primește picks diferite)
- **Optimizare automată** pentru probabilitate combinată și EV
- **Configurare flexibilă** (număr selecții, interval cote)
- **Metrici detaliate** per selecție și total parlay

### 🌐 **Interfață Modernă**
- **Multilingv**: Română 🇷🇴, English 🇬🇧, Русский 🇷🇺
- **Meniu intuitiv** cu butoane și emoji
- **Comutare limbă** fără restart
- **Welcome experience** cu animație (opțional)
- **Match insights** cu 🧠 emoji și informații contextualizate

### 📈 **Învățare Locală**
- **Logging CSV** pentru toate predicțiile
- **Etichetare automată** a rezultatelor zilnic
- **Training modele ML** din date istorice
- **Blend inteligent** cote + formă + ML (80% + 20% implicit)

### 🏥 **Monitorizare & Resilience**
- **Health check** pentru toate API-urile (status OK/MISSING)
- **Caching TTL** (60-120s) pentru performanță
- **Graceful degradation** dacă API-urile nu răspund
- **Rate limiting awareness** pentru planurile gratuite

## 🚀 Configurare Rapidă

### 1. **Chei API** (completează în `.env`):
```env
# === CORE APIS (Obligatorii) ===
TELEGRAM_BOT_TOKEN=your_telegram_token
FOOTBALL_DATA_TOKEN=your_fd_token          # Free forever - football-data.org
ODDS_API_KEY=your_odds_api_key             # Free 500 calls/lună - the-odds-api.com

# === STATISTICI ÎMBUNĂTĂȚITE ===
API_FOOTBALL_KEY=your_api_sports_key       # Preferat - api-sports.io
APIFOOTBALL_KEY=your_apifootball_key       # Fallback - apifootball.com

# === DATE CONTEXTUALE ===
OPENWEATHER_KEY=your_openweather_key       # Condiții meteo
VIDEO_API_TOKEN=your_video_token           # Highlights (placeholder)

# === SENTIMENT ANALYSIS ===
REDDIT_CLIENT_ID=your_reddit_client
REDDIT_CLIENT_SECRET=your_reddit_secret
REDDIT_USER_AGENT=PariuSmart-Bot/1.0

# === OPȚIONAL ===
GDELT_ENABLED=1                            # Analiza știrilor internaționale
```

### 2. **Instalare**:
```bash
# Clonează și setup mediu virtual
git clone <repo-url>
cd free-soccer-telegram-bot
python -m venv .venv

# Activare (Linux/Mac)
source .venv/bin/activate
# SAU Windows
.venv\Scripts\activate

# Instalare dependențe
pip install -r requirements.txt
```

### 3. **Rulare**:
```bash
# Dezvoltare locală
python -m bot.bot

# SAU folosind modulul
python bot/bot.py
```

## 📱 Comenzi Bot

### Comenzi Principale
- `/start` → Mesaj de bun venit cu interfață modernă și animație
- `/today` → **TOP 2 picks 1X2** personalizate cu EV calculation  
- `/markets` → **Piețe O/U 2.5 & BTTS** cu procente mari
- `/all` → **🌟 PREDICȚII COMPLETE** pentru toate piețele (nou!)
- `/express [min] [max] [legs]` → **Expresuri rapide** optimizate AI
- `/health` → **Status toate API-urile** (OK/MISSING, fără a afișa chei)
- `/lang` → **Comută limba** cu steaguri (🇷🇴🇬🇧🇷🇺)

### Meniu Interactiv Modern
- � **Picks Azi** → Cele mai bune 2 selecții 1X2 cu probabilități
- 📊 **Piețe (O/U & BTTS)** → 3-4 picks mixte cu EV pozitiv  
- � **Predicții Complete** → Match cards cu toate piețele (nou!)
- �🎯 **Expres** → Wizard configurabil cu setări vizuale
- 🌐 **Limba** → Română/English/Русский cu steaguri 
- ℹ️ **Ajutor** → Ghid complet comenzi cu explicații AI

### 🌟 Noutăți Interface Modernă
- **Match Cards** → Afișaj frumos cu toate probabilitățile
- **Butoane interactive** cu emoji și indicatori vizuali
- **Predicții pentru toate piețele** → 1X2, O/U 2.5, BTTS în același loc
- **EV calculation** vizibil pentru fiecare selecție
- **Best pick recommendation** → AI îți spune cea mai bună opțiune
- **Visual indicators** → 🔥 pentru EV mare, ⭐ pentru EV mediu, 💫 pentru EV mic

## 🏗️ Arhitectura Tehnică

### **Fetchers (Colectare Date)**
- `football_data.py` → Meciuri și rezultate (caching 5 min)
- `odds_api.py` → Cote H2H/O/U/BTTS (caching 90s)
- `api_football.py` → Statistici echipe (caching 10 min)
- `weather.py` → Condiții meteo (caching 2h)
- `reddit.py` + `gdelt.py` → Sentiment analysis (caching 1h)

### **Analytics (Procesare)**
- `probability.py` → Blend probabilități cote + formă
- `markets.py` → Normalizare picks O/U și BTTS
- `insights.py` → Generare match insights contextuale
- `express.py` → Optimizare expresuri high-prob

### **AI & ML**
- `predictions_logger.py` → CSV logging toate predicțiile
- `label_results.py` → Etichetare automată rezultate
- `model_blend.py` → Integrare modele ML locale

### **Utils**
- `config.py` → Configurare centralizată + health check
- `cache.py` → TTL caching thread-safe  
- `i18n.py` → Traduceri RO/EN/RU complete

## 🚀 Deployment Producție

### **Windows - Rulare Permanentă (Task Scheduler)**

Pentru a rula botul permanent pe Windows cu repornire automată:

#### **Pași de Instalare:**

1. **Deschide PowerShell ca Administrator**
   ```powershell
   # Click dreapta pe Start → "Windows PowerShell (Administrator)"
   ```

2. **Setează Execution Policy (pe sesiune)**
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   ```

3. **Navighează la directorul botului și instalează taskul**
   ```powershell
   cd "C:\Users\Bogdan\Downloads\free-soccer-telegram-bot"
   .\deploy\install_task_windows.ps1 -RepoPath "C:\Users\Bogdan\Downloads\free-soccer-telegram-bot"
   ```

4. **Pornește taskul**
   ```powershell
   Start-ScheduledTask -TaskName "PariuSmartAIBot"
   ```

#### **Verificare și Monitorizare:**

```powershell
# Verifică statusul taskului
Get-ScheduledTaskInfo -TaskName "PariuSmartAIBot"

# Monitorizează logurile live
Get-Content .\logs\bot.log -Tail 100 -Wait

# Verifică ultimele 50 linii din log
Get-Content .\logs\bot.log -Tail 50
```

#### **Test Manual:**

```powershell
# Test rulare script (pentru debugging)
.\deploy\run_windows.ps1
```

#### **Dezinstalare (Opțional):**

```powershell
.\deploy\uninstall_task_windows.ps1
```

#### **Caracteristici Avansate:**
- ✅ **Auto-restart** la crash (până la 10 încercări/minut)
- ✅ **Start la boot** și la logon
- ✅ **Logging complet** în `logs\bot.log`
- ✅ **Virtual environment** auto-creat și activat
- ✅ **Dependencies** auto-instalate
- ✅ **Rulare în buclă** cu restart în caz de eroare

### **Linux (Systemd)**
```bash
# Rulează script automat
chmod +x deploy/deploy_linux.sh
./deploy/deploy_linux.sh

# SAU manual:
sudo cp deploy/pariusmart.service /etc/systemd/system/
sudo systemctl enable --now pariusmart
```

### **Windows (Task Scheduler/NSSM)**
```powershell
# Instalează NSSM (Non-Sucking Service Manager)
# Download de la: https://nssm.cc/download

# Instalare serviciu
nssm install PariuSmartBot "C:\path\to\.venv\Scripts\python.exe"
nssm set PariuSmartBot Arguments "-m bot.bot"
nssm set PariuSmartBot AppDirectory "C:\path\to\bot"
nssm set PariuSmartBot DisplayName "PariuSmart AI Bot"
nssm set PariuSmartBot Description "Advanced sports betting AI agent"

# Start serviciu
nssm start PariuSmartBot
```

### **Monitorizare**
```bash
# Status serviciu
sudo systemctl status pariusmart

# Loguri live
sudo journalctl -u pariusmart -f

# Etichetare rezultate zilnică (cron)
0 2 * * * cd /opt/pariusmart-bot && ./.venv/bin/python tools/label_results.py
```

## 📊 Exemple Utilitate

### **Match Insights Avansate**
```
🧠 ⚽ High-scoring teams (3.2 avg goals) • ⭐ Key players: Haaland, Salah • 
🌤️ 18°C, 3m/s wind • 🟢 Positive buzz (12 sources)
```

### **Markets Display**
```
📊 2024-09-25 — O/U 2.5 & BTTS

• Arsenal vs Chelsea — O/U 2.5: Over 2.5 | p≈62.4% | cote 1.75 | EV +0.092
• Liverpool vs City — BTTS: Yes | p≈71.2% | cote 1.65 | EV +0.175  
• Madrid vs Barcelona — O/U 2.5: Over 2.5 | p≈58.1% | cote 1.80 | EV +0.046
```

### **Express Optimizat**
```
🎯 2024-09-25 — Expres (3 selecții)

• Arsenal vs Chelsea — 1X2: Arsenal | p≈0.524 | cote 1.85
• Bayern vs Dortmund — 1X2: Bayern | p≈0.612 | cote 1.72  
• PSG vs Lyon — 1X2: PSG | p≈0.681 | cote 1.51

Prob combinată≈0.218 | Cote totale 4.81 | EV +0.049
```

## 🔐 Securitate & Compliance

- **Niciodată nu afișează chei API** în logs sau mesaje
- **Rate limiting** automat pentru toate API-urile
- **Validare input** pentru comenzi utilizator
- **Disclaimer 18+** în toate mesajele relevante
- **Graceful failure** când API-urile nu sunt disponibile

## 📈 Scalare Viitoare

- [ ] **Dashboard web** (FastAPI + React) pentru analiză avansată
- [ ] **Sistem abonamente** (Stripe) pentru features premium  
- [ ] **Modele ML** mai complexe (XGBoost, ensemble)
- [ ] **Piețe suplimentare** (corners, cartonașe, handicap)
- [ ] **Live betting** cu updates timp real
- [ ] **Portfolio management** cu bankroll tracking

## 🔒 Abonamente (MVP fără server)

### Configurare Manuală Coduri Promo

Pentru a adăuga coduri promo, editează manual `data/subscriptions.json`:

```json
{
  "admins": [123456789],
  "users": {},
  "codes": {
    "PROMO30": {"plan": "starter", "days": 30},
    "VIP90": {"plan": "pro", "days": 90}
  }
}
```

### Comenzi Abonamente

- `/subscribe` → Afișează planuri disponibile cu linkuri de plată
- `/redeem CODUL_TĂU` → Activează abonament cu cod promo
- `/status` → Verifică planul curent și data expirării  
- `/grant <zile> <plan> <id_user>` → Doar admin; acordă zile unui utilizator

### Planuri Disponibile

- **Free**: Acces limitat la `/today`
- **Starter** (€9.99/lună): Acces la `/markets`, expres max 3 selecții
- **Pro** (€19.99/lună): Acces complet, expres max 4 selecții

### Integrare Viitoare

Ulterior vom integra:
- **Stripe/Telegram Payments** cu webhook automat
- **Portal self-service** pentru gestionare abonamente
- **Analytics avansate** per plan de utilizator

## ⚠️ Disclaimer Legal

**Pariurile implică riscuri financiare semnificative. Vârsta minimă: 18 ani.**

- Nu garantăm profituri sau acuratețea predicțiilor
- Utilizează doar bani pe care îți permiți să-i pierzi  
- Respectă legislația locală privind pariurile online
- Joacă responsabil și cere ajutor dacă dezvolți dependență

Bot-ul este destinat **exclusiv scopurilor educaționale și de divertisment**.

**Documente legale**: [Termeni](TERMS.md) | [Privacy](PRIVACY.md) | [Disclaimer](DISCLAIMER.md)

---

**Dezvoltat cu ❤️ pentru comunitatea de betting inteligent**