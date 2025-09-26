#!/bin/bash
# PariuSmart AI Bot - Quick Deploy Script for Linux/macOS

set -e

echo "🚀 PariuSmart AI Bot - Quick Deploy"
echo "=================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before continuing!"
    echo "   TELEGRAM_BOT_TOKEN - Get from @BotFather"
    echo "   FOOTBALL_DATA_TOKEN - Get from football-data.org"
    echo "   ODDS_API_KEY - Get from the-odds-api.com"
    echo ""
    read -p "Press Enter after you've configured your .env file..."
fi

# Check if Docker is installed
if command -v docker &> /dev/null; then
    echo "🐳 Docker found! Using Docker deployment..."
    
    # Build and run with Docker
    echo "📦 Building Docker image..."
    docker build -t pariusmart-bot .
    
    echo "🏃 Starting container..."
    docker run -d \
        --name pariusmart-ai \
        --restart unless-stopped \
        --env-file .env \
        -v $(pwd)/data:/app/data \
        -v $(pwd)/logs:/app/logs \
        -v $(pwd)/storage:/app/storage \
        pariusmart-bot
    
    echo "✅ Bot deployed successfully with Docker!"
    echo "📊 Check status: docker ps"
    echo "📝 View logs: docker logs -f pariusmart-ai"
    
elif command -v python3 &> /dev/null; then
    echo "🐍 Python found! Using Python deployment..."
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install requirements
    echo "📦 Installing requirements..."
    pip install -r requirements.txt
    
    # Create systemd service (Linux only)
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "⚙️ Creating systemd service..."
        
        SERVICE_FILE="/etc/systemd/system/pariusmart-bot.service"
        BOT_PATH=$(pwd)
        USER=$(whoami)
        
        sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=PariuSmart AI Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_PATH
Environment=PATH=$BOT_PATH/venv/bin
ExecStart=$BOT_PATH/venv/bin/python -m bot.bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable pariusmart-bot
        sudo systemctl start pariusmart-bot
        
        echo "✅ Bot deployed as systemd service!"
        echo "📊 Check status: sudo systemctl status pariusmart-bot"
        echo "📝 View logs: sudo journalctl -u pariusmart-bot -f"
        
    else
        # macOS - just run directly
        echo "🍎 macOS detected - running bot directly..."
        echo "💡 For permanent deployment, consider using Docker or a cloud service"
        
        # Run in background
        nohup python -m bot.bot > logs/bot.log 2>&1 &
        echo $! > bot.pid
        
        echo "✅ Bot started in background!"
        echo "📝 View logs: tail -f logs/bot.log"
        echo "🛑 Stop bot: kill \$(cat bot.pid)"
    fi
    
else
    echo "❌ Neither Docker nor Python3 found!"
    echo "Please install Docker or Python 3.8+ and try again"
    exit 1
fi

echo ""
echo "🎉 Deployment complete!"
echo "💬 Your bot should now be running 24/7"
echo "📱 Test it by sending /start to your bot on Telegram"