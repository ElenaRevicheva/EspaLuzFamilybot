#!/usr/bin/env python3
"""
Telegram Bot Webhook Killer - Runs as a separate service to constantly
monitor and remove webhooks that might appear
"""
import os
import time
import requests
import logging
import sys
import traceback
from dotenv import load_dotenv

# Extremely visible logging for debugging
print("🔥🔥🔥 BOT-KILLER.PY LOADED 🔥🔥🔥")

# Configure logging with emojis for visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - 🛡️ BOT-KILLER - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bot-killer')

# Load environment variables
load_dotenv()

def nuke_webhook():
    """Aggressively and forcefully delete any webhook"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found! Bot-killer cannot run!")
        return False
    
    try:
        # Build URLs
        delete_url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
        info_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
        
        # Step 1: Delete webhook
        logger.info("Performing webhook deletion...")
        delete_response = requests.get(delete_url, timeout=30)
        delete_result = delete_response.json()
        logger.info(f"Deletion result: {delete_result}")
        
        # Step 2: Verify webhook is gone
        info_response = requests.get(info_url, timeout=30)
        info_result = info_response.json()
        
        # Check if webhook is actually gone
        webhook_url = info_result.get('result', {}).get('url', '')
        
        if webhook_url:
            logger.warning(f"WEBHOOK STILL EXISTS: {webhook_url}!")
            logger.warning("Forceful deletion unsuccessful - will try again")
            return False
        else:
            logger.info("Webhook successfully deleted (or was already gone)")
            return True
            
    except Exception as e:
        logger.error(f"Error during webhook deletion: {e}")
        traceback.print_exc()
        return False

def main():
    """Main daemon function that continuously checks for webhooks"""
    logger.info("===== Bot Killer Service Starting =====")
    logger.info("This service will continuously monitor and remove webhooks")
    
    # Initial deletion attempt
    logger.info("Performing initial webhook removal...")
    nuke_webhook()
    
    # Continuous monitoring
    cycle = 0
    while True:
        try:
            cycle += 1
            logger.info(f"Webhook check cycle #{cycle}")
            
            # Check and delete webhook
            nuke_webhook()
            
            # Wait before next check (30 seconds)
            logger.info(f"Waiting 30 seconds before next webhook check...")
            time.sleep(30)
            
        except KeyboardInterrupt:
            logger.info("Bot killer service shutting down")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.error(traceback.format_exc())
            time.sleep(60)  # Wait longer after errors

if __name__ == "__main__":
    main()
