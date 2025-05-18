#!/bin/bash

echo "====== STARTING BOT SERVICES ======="

# First, forcefully ensure webhook is removed
echo "Initial webhook removal..."
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/deleteWebhook?drop_pending_updates=true"
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo"

# Wait to ensure changes propagate
echo "Waiting for API changes to propagate..."
sleep 5

# Start bot-killer in background
echo "Starting bot-killer monitoring service..."
python bot-killer.py &
BOT_KILLER_PID=$!
echo "Bot killer started with PID: $BOT_KILLER_PID"

# Wait a bit for bot-killer to initialize
sleep 5

# Start main bot
echo "Starting main bot..."
python main.py
