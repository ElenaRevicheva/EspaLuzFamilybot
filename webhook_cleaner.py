import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get your bot token
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# Step 1: Delete existing webhook (if any)
url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true"
response = requests.get(url)
print(f"Webhook deletion response: {response.json()}")

# Step 2: Confirm webhook is cleared
check_url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
webhook_info = requests.get(check_url).json()
print(f"Webhook info: {webhook_info}")
