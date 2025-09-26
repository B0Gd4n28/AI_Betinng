# 🌐 PariuSmart AI Bot - Cloud Deployment Guide

## 🚀 Deploy pe Railway (GRATUIT - RECOMANDAT)

### Pasul 1: Pregătire Repository
```bash
git add .
git commit -m "Ready for Railway deployment"
git push origin main
```

### Pasul 2: Deploy pe Railway
1. Mergi la [railway.app](https://railway.app)
2. Sign up cu GitHub
3. Apasă "New Project" → "Deploy from GitHub repo"
4. Selectează `free-soccer-telegram-bot`
5. Railway va detecta automat `Dockerfile`

### Pasul 3: Configurare Environment Variables
În Railway Dashboard → Settings → Environment:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
FOOTBALL_DATA_TOKEN=your_football_data_token
ODDS_API_KEY=your_odds_api_key
OPENWEATHER_API_KEY=your_weather_key
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret
GDELT_API_KEY=your_gdelt_key
```

### Pasul 4: Deploy
- Railway va face deploy automat
- Botul va rula 24/7 GRATUIT (500 ore/lună)
- Auto-restart dacă se oprește

---

## 🐳 Deploy cu Docker (Local sau VPS)

### Local cu Docker:
```bash
# Build image
docker build -t pariusmart-bot .

# Run container
docker run -d \
  --name pariusmart-ai \
  --restart unless-stopped \
  --env-file .env \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  pariusmart-bot
```

### Cu Docker Compose:
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## ☁️ Alte Opțiuni Cloud

### Heroku (Plătit):
1. `heroku create pariusmart-bot`
2. `heroku config:set TELEGRAM_BOT_TOKEN=your_token`
3. `git push heroku main`

### DigitalOcean (VPS $5/lună):
1. Creează Droplet Ubuntu
2. Instalează Docker
3. Clone repo + docker-compose up -d

### Google Cloud Run (Pay-per-use):
1. `gcloud builds submit --tag gcr.io/PROJECT-ID/pariusmart`
2. `gcloud run deploy --image gcr.io/PROJECT-ID/pariusmart`

---

## 💻 Windows Service (Rulare locală permanentă)

Pentru Windows, am creat script în `deploy/windows/`:
```powershell
# Instalează ca Windows Service
.\deploy\windows\install_service.ps1

# Start service
Start-Service PariuSmartBot

# Check status
Get-Service PariuSmartBot
```

---

## 🔧 Monitoring & Logs

### Railway Dashboard:
- Live logs în timp real
- Metrics (CPU, RAM)
- Auto-scaling

### Docker Logs:
```bash
docker logs -f pariusmart-ai
```

### Status Check:
```bash
curl https://your-railway-app.railway.app/health
```

---

## 🎯 RECOMANDAT: Railway.app

**De ce Railway?**
✅ 500 ore gratuite/lună (suficient pentru bot 24/7)  
✅ Deploy automat din GitHub  
✅ Environment variables securizate  
✅ Auto-restart dacă se oprește  
✅ Logs și monitoring gratuit  
✅ Scaling automat  
✅ Domain gratuit inclus  

**Cost:** $0/lună pentru usage normal

---

## 🚨 Important pentru Producție

1. **Environment Variables**: Nu pune niciodată token-urile în cod
2. **Monitoring**: Configurează alerts pentru downtime
3. **Backup**: Data folder backup automat
4. **Logs**: Păstrează logs pentru debugging
5. **Updates**: Auto-deploy la fiecare git push