#!/usr/bin/env python3
"""
🤖⚽ PariuSmart AI - Setup Script
Configurare rapidă pentru administratori
"""

import json
import os
from datetime import datetime, timedelta

def setup_admin():
    """Setup script for quick admin configuration"""
    print("🤖⚽ PariuSmart AI - Configurare Rapidă")
    print("=" * 50)
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Get admin ID
    while True:
        try:
            admin_id = int(input("📱 Introdu ID-ul tău Telegram (admin): "))
            break
        except ValueError:
            print("❌ ID invalid. Încearcă din nou.")
    
    # Create subscriptions.json with admin
    subs_data = {
        "admins": [admin_id],
        "users": {},
        "codes": {
            "WELCOME7": {"plan": "starter", "days": 7},
            "VIP30": {"plan": "pro", "days": 30},
            "TEST": {"plan": "starter", "days": 1}
        }
    }
    
    with open('data/subscriptions.json', 'w', encoding='utf-8') as f:
        json.dump(subs_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Admin {admin_id} configurat!")
    print("✅ Coduri promo create: WELCOME7, VIP30, TEST")
    
    # Check .env file
    if not os.path.exists('.env'):
        print("\n⚠️  Fișierul .env nu există!")
        create_env = input("Vrei să creez .env cu template? (y/n): ").lower() == 'y'
        if create_env:
            env_template = """# PariuSmart AI Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
FOOTBALL_DATA_TOKEN=your_football_data_token
ODDS_API_KEY=your_odds_api_key

# Optional APIs
API_FOOTBALL_KEY=
OPENWEATHER_KEY=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=PariuSmart-Bot/1.0
"""
            with open('.env', 'w') as f:
                f.write(env_template)
            print("✅ Template .env creat! Completează token-urile.")
    
    print("\n🚀 Configurare completă!")
    print("📋 Următorii pași:")
    print("1. Completează .env cu token-urile")
    print("2. Rulează: python -m bot.bot")
    print("3. Testează /admin în Telegram")
    print("4. Distribuie codurile: WELCOME7, VIP30, TEST")

if __name__ == "__main__":
    setup_admin()