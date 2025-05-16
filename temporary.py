
import requests
import os

token = os.environ["TELEGRAM_BOT_TOKEN"]
url = f"https://espa-luz-familybot-elenarevicheva2.replit.app/{token}"

# First remove any existing webhook
requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook")

# Set new webhook with proper parameters
r = requests.get(
    f"https://api.telegram.org/bot{token}/setWebhook",
    params={
        "url": url,
        "allowed_updates": ["message", "edited_message", "callback_query"]
    }
)
print(r.text)
