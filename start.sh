#!/bin/bash

echo "=== RAILWAY TELEGRAM BOT STARTUP ==="

# First, aggressively clear the webhook with dedicated script
echo "Step 1: Clearing webhook (forceful method)..."
python webhook_deleter.py

# If webhook deletion fails, try direct curl approach
if [ $? -ne 0 ]; then
    echo "Trying direct curl webhook deletion..."
    curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/deleteWebhook?drop_pending_updates=true"
    curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo"
fi

# Wait for webhook deletion to settle
echo "Step 2: Waiting for Telegram API to process deletion..."
sleep 10

# Make one more verification
echo "Step 3: Verifying webhook is gone..."
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo"

# Start the bot with polling
echo "Step 4: Starting bot with polling..."
python main.py
