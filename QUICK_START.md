# 🤖⚽ PariuSmart AI - Ghid Rapid

## 🚀 Start în 3 Pași

### 1. Configurare Admin
```bash
python setup.py
```
- Adaugă ID-ul tău Telegram ca admin
- Creează coduri promo automat
- Generează template .env

### 2. Completează Token-urile
Editează `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
FOOTBALL_DATA_TOKEN=your_football_data_token
ODDS_API_KEY=your_odds_api_key
```

### 3. Pornește Botul
```bash
python -m bot.bot
```

## 📱 Comenzi Pentru Utilizatori

### 🔓 Gratuite (Toți Utilizatorii)
- `/start` - Mesaj de bun venit cu status plan
- `/today` - Cele mai bune 2 picks zilnice
- `/help` - Ghid complet comenzi
- `/status` - Verifică abonamentul

### 🔒 Premium (Starter/Pro)
- `/markets` - Piețe O/U 2.5 & BTTS
- `/express` - Expresuri inteligente (3-4 selecții)
- `/stats` - Analytics personal și ROI
- `/bankroll` - Management fonduri Kelly

### 👑 Admin
- `/admin` - Panel admin cu coduri promo
- `/grant <zile> <plan> <user_id>` - Acordă abonament

## 💰 Planuri Abonament

| Plan | Funcții | Preț |
|------|---------|------|
| **Free** | `/today` + help | Gratis |
| **Starter** | Markets + Express (3) | €9.99/lună |
| **Pro** | Toate + Analytics | €19.99/lună |

## 🎁 Coduri Promo Default

După `python setup.py` ai automat:
- `WELCOME7` - 7 zile Starter
- `VIP30` - 30 zile Pro  
- `TEST` - 1 zi Starter

## 🛠️ Gestionare Avansată

### Adăugare Coduri Noi
Editează `data/subscriptions.json`:
```json
{
  "codes": {
    "WEEKEND": {"plan": "starter", "days": 2},
    "PROMO50": {"plan": "pro", "days": 50}
  }
}
```

### Rulare Permanent
**Windows:**
```powershell
.\deploy\install_task_windows.ps1
```

**Linux:**
```bash
sudo systemctl enable --now pariusmart
```

## 📊 Monitorizare

- **Loguri**: `logs/bot.log`
- **Stats**: `storage/user_stats.json`
- **Utilizatori**: `data/subscriptions.json`

## 🆘 Troubleshooting

**Bot nu pornește?**
- Verifică `.env` are token-urile
- Rulează `python setup.py` din nou

**Comenzi nu funcționează?**
- Verifică dacă ești admin în `data/subscriptions.json`
- Testează `/status` pentru planul curent

**Coduri promo nu funcționează?**
- Verifică sintaxa JSON în `data/subscriptions.json`
- Codurile sunt case-sensitive

---
**Pentru documentație completă vezi [README.md](README.md) și [USER_GUIDE.md](USER_GUIDE.md)**