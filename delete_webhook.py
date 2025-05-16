
import requests
import os

token = os.environ["TELEGRAM_BOT_TOKEN"]
r = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook")
print("🔌 Webhook deletion response:", r.text)
