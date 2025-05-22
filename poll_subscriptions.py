import requests
import json
import os
import time
from datetime import datetime

ACCESS_TOKEN = os.getenv("GUMROAD_ACCESS_TOKEN")
PRODUCT_ID = os.getenv("GUMROAD_PRODUCT_ID")
DB_FILE = "subscribers.json"

def fetch_all_subscriptions():
    url = f"https://api.gumroad.com/v2/products/{PRODUCT_ID}/subscriptions"
    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    subscriptions = []
    page = 1
    while True:
        response = requests.get(url, headers=headers, params={'page': page})
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code} - {response.text}")
            break
        data = response.json()
        subs = data.get('subscriptions', [])
        if not subs:
            break
        subscriptions.extend(subs)
        page += 1
    return subscriptions

def update_subscriber_file(subscriptions):
    print(f"📦 Updating {DB_FILE} with {len(subscriptions)} subscriptions...")
    db = {}

    # Load existing subscriber data
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                db = json.load(f)
            except json.JSONDecodeError:
                db = {}

    # Update each subscription
    for sub in subscriptions:
        email = sub['email'].lower()
        status = "active"
        if sub.get("ended_at") or sub.get("cancelled_at") or sub.get("failed_at"):
            status = "inactive"

        db[email] = {
            "subscription_id": sub["id"],
            "status": status,
            "last_checked": datetime.utcnow().isoformat(),
            "telegram_id": db.get(email, {}).get("telegram_id")  # preserve existing ID if present
        }

    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)
    print("✅ Subscription database updated.")

def main():
    while True:
        try:
            print(f"\n🔄 Polling Gumroad API at {datetime.utcnow().isoformat()}...")
            subscriptions = fetch_all_subscriptions()
            update_subscriber_file(subscriptions)
        except Exception as e:
            print(f"❌ Error during polling: {e}")
        time.sleep(3600)  # Poll every hour

if __name__ == "__main__":
    main()
