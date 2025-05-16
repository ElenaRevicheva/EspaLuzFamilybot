
import requests
import os
import time
import json

token = os.environ["TELEGRAM_BOT_TOKEN"]
url = f"https://espa-luz-familybot-elenarevicheva2.replit.app/{token}"

print("Checking bot status...")
me_response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
print("Bot info:", me_response.text)

print("\nChecking updates...")
updates_response = requests.get(f"https://api.telegram.org/bot{token}/getUpdates")
print("Recent updates:", updates_response.text)

# First remove any existing webhook
response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook")
print("Delete webhook response:", response.text)

# Wait a moment
time.sleep(2)

# Set new webhook with proper parameters
webhook_data = {
    "url": url,
    "allowed_updates": ["message", "edited_message", "callback_query"],
    "drop_pending_updates": True
}

response = requests.post(
    f"https://api.telegram.org/bot{token}/setWebhook",
    json=webhook_data
)
print("Set webhook response:", response.text)

# Verify webhook info
info_response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
print("Webhook info:", info_response.text)
