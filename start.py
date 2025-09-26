#!/usr/bin/env python3
"""
Railway.app startup script for PariuSmart AI Bot
"""
import os
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Start the bot"""
    try:
        logger.info("🚀 Starting PariuSmart AI Bot on Railway...")
        
        # Check environment variables
        required_vars = ['TELEGRAM_BOT_TOKEN', 'FOOTBALL_DATA_TOKEN']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            sys.exit(1)
        
        logger.info("✅ Environment variables check passed")
        
        # Import and run bot
        from bot.bot import main as bot_main
        logger.info("✅ Bot module imported successfully")
        
        bot_main()
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()