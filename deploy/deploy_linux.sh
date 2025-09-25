#!/bin/bash
# Linux deployment script for PariuSmart AI Bot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}PariuSmart AI Bot - Linux Deployment Script${NC}"
echo "=============================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}Error: Don't run this script as root!${NC}"
   exit 1
fi

# Configuration
BOT_USER="pariusmart"
BOT_DIR="/opt/pariusmart-bot"
SERVICE_NAME="pariusmart"

# Check if user exists
if ! id "$BOT_USER" &>/dev/null; then
    echo -e "${YELLOW}Creating user $BOT_USER...${NC}"
    sudo useradd -r -s /bin/false -d $BOT_DIR $BOT_USER
fi

# Create directories
echo -e "${YELLOW}Setting up directories...${NC}"
sudo mkdir -p $BOT_DIR/{data,model,assets,logs}
sudo chown -R $BOT_USER:$BOT_USER $BOT_DIR

# Copy application files
echo -e "${YELLOW}Copying application files...${NC}"
sudo cp -r bot/ src/ requirements.txt tools/ deploy/ $BOT_DIR/
sudo cp .env $BOT_DIR/ 2>/dev/null || echo -e "${YELLOW}Warning: .env file not found. Please create it manually.${NC}"

# Set permissions
sudo chown -R $BOT_USER:$BOT_USER $BOT_DIR
sudo chmod +x $BOT_DIR/tools/*.py

# Install Python and dependencies
echo -e "${YELLOW}Setting up Python environment...${NC}"
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
sudo -u $BOT_USER python3 -m venv $BOT_DIR/.venv

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
sudo -u $BOT_USER $BOT_DIR/.venv/bin/pip install -r $BOT_DIR/requirements.txt

# Install systemd service
echo -e "${YELLOW}Installing systemd service...${NC}"
sudo cp $BOT_DIR/deploy/pariusmart.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start service
echo -e "${YELLOW}Enabling and starting service...${NC}"
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# Check status
sleep 2
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}✓ Service started successfully!${NC}"
else
    echo -e "${RED}✗ Service failed to start. Check logs:${NC}"
    echo "sudo journalctl -u $SERVICE_NAME -n 20"
    exit 1
fi

# Setup log rotation
echo -e "${YELLOW}Setting up log rotation...${NC}"
sudo tee /etc/logrotate.d/pariusmart > /dev/null <<EOF
$BOT_DIR/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 644 $BOT_USER $BOT_USER
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF

# Setup cron for result labeling
echo -e "${YELLOW}Setting up daily result labeling...${NC}"
sudo -u $BOT_USER crontab -l 2>/dev/null | { cat; echo "0 2 * * * cd $BOT_DIR && ./.venv/bin/python tools/label_results.py >> logs/labeling.log 2>&1"; } | sudo -u $BOT_USER crontab -

echo -e "${GREEN}"
echo "=============================================="
echo "✓ PariuSmart AI Bot deployed successfully!"
echo "=============================================="
echo -e "${NC}"
echo "Service status: sudo systemctl status $SERVICE_NAME"
echo "View logs:      sudo journalctl -u $SERVICE_NAME -f"
echo "Restart:        sudo systemctl restart $SERVICE_NAME"
echo "Stop:           sudo systemctl stop $SERVICE_NAME"
echo ""
echo -e "${YELLOW}Don't forget to:${NC}"
echo "1. Configure your .env file in $BOT_DIR/.env"
echo "2. Test the bot with: sudo -u $BOT_USER $BOT_DIR/.venv/bin/python -m bot.bot"
echo "3. Check /health command in Telegram"