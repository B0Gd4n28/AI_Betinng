# 🤖⚽ PariuSmart AI - Configurare Utilizatori

## 🔧 Setări Rapide

### 1. Configurarea Botului
```env
# Copiază .env.example ca .env și completează:
TELEGRAM_BOT_TOKEN=your_bot_token_here
FOOTBALL_DATA_TOKEN=your_football_data_token
ODDS_API_KEY=your_odds_api_key
```

### 2. Adăugarea Adminilor
Editează `data/subscriptions.json`:
```json
{
  "admins": [123456789, 987654321],
  "users": {},
  "codes": {}
}
```

### 3. Coduri Promo
Adaugă coduri în `data/subscriptions.json`:
```json
{
  "codes": {
    "WELCOME30": {"plan": "starter", "days": 30},
    "VIP90": {"plan": "pro", "days": 90},
    "PROMO7": {"plan": "starter", "days": 7}
  }
}
```

## 🚀 Comenzi Disponibile

### Comenzi Principale
- `/start` - Pornește botul cu meniu interactiv
- `/today` - Cele mai bune 2 picks pentru azi
- `/markets` - Piețe Over/Under și BTTS
- `/express` - Expresuri inteligente personalizate

### Funcții Avansate  
- `/stats` - Statistici personale și analytics
- `/bankroll` - Management fonduri cu Kelly Criterion
- `/live` - Center live cu notificări
- `/strategies` - Instrumente avansate (arbitrage, value bets)

### Abonamente
- `/subscribe` - Vezi planurile disponibile
- `/redeem COD` - Activează abonament cu cod promo
- `/status` - Verifică planul curent
- `/grant <zile> <plan> <user_id>` - Doar admini

## 📊 Planuri Abonament

| Plan | Preț | Funcții |
|------|------|---------|
| **Free** | Gratis | Acces la `/today` |
| **Starter** | €9.99/lună | Toate piețele, expres 3 selecții |
| **Pro** | €19.99/lună | Acces complet, expres 4 selecții |

## 🛠️ Instrucțiuni pentru Admini

### Acordarea de Abonamente
```
/grant 30 starter 123456789  # 30 zile Starter
/grant 90 pro 987654321      # 90 zile Pro
```

### Monitorizare Utilizatori
- Verifică `storage/user_stats.json` pentru analytics
- Urmărește `logs/bot.log` pentru activitate
- Gestionează codurile în `data/subscriptions.json`

## 🚀 Pornire Rapidă

### Dezvoltare Locală
```bash
python -m bot.bot
```

### Serviciu Permanent (Windows)
```powershell
# Ca Administrator
.\deploy\install_task_windows.ps1
Start-ScheduledTask -TaskName "PariuSmartAIBot"
```

### Serviciu Permanent (Linux)
```bash
sudo systemctl enable --now pariusmart
```

## 📱 Testare Funcționalități

1. **Trimite `/start` în Telegram**
2. **Testează `/today` pentru picks**
3. **Încearcă `/redeem` cu un cod promo**
4. **Verifică `/status` pentru planul activ**

---
**Pentru suport tehnic, verifică documentele legale: [Termeni](TERMS.md) | [Privacy](PRIVACY.md) | [Disclaimer](DISCLAIMER.md)**