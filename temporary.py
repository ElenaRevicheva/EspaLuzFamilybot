import requests
import os

token = os.environ["TELEGRAM_BOT_TOKEN"]
url = f"https://espa-luz-familybot-elenarevicheva2.replit.app/{token}"
r = requests.get(f"https://api.telegram.org/bot{token}/setWebhook?url={url}")
print(r.text)
