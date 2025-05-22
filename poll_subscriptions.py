import requests
import json
import os
import time
from datetime import datetime

ACCESS_TOKEN = os.getenv("GUMROAD_ACCESS_TOKEN")
PRODUCT_ID = os.getenv("GUMROAD_PRODUCT_ID")
DB_FILE = "subscribers.json"

def fetch_all_subscribers():
    url = f"https://api.gumroad.com/v2/products/{PRODUCT_ID}/subscribers"
    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    subscribers = []
    page = 1
    while True:
        response = requests.get(url, headers=headers, params={'page': page})
        print(f"📥 Raw API response page {page}: {response.status_code} - {response.text[:300]}")
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code} - {response.text}")
            break
        data = response.json()
        subs = data.get('subscribers', [])
        if not subs:
            break

        # ✅ Detect duplicates by ID
        existing_ids = {s['id'] for s in subscribers}
        new_subs = [s for s in subs if s['id'] not in existing_ids]

        if not new_subs:
            print("⚠️ No new subscribers found — stopping pagination.")
            break

        subscribers.extend(new_subs)
        page += 1

    return subscribers

def update_subscriber_file(subscribers):
    print(f"📦 Updating {DB_FILE} with {len(subscribers)} subscribers...")
    db = {}

    # Load existing subscriber data
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                db = json.load(f)
            except json.JSONDecodeError:
                db = {}

    for sub in subscribers:
        email = sub['email'].lower()
        status = "active"
        if sub.get("subscription_ended_at") or sub.get("subscription_cancelled_at") or sub.get("subscription_failed_at"):
            status = "inactive"

        db[email] = {
            "subscriber_id": sub["id"],
            "status": status,
            "last_checked": datetime.utcnow().isoformat(),
            "telegram_id": db.get(email, {}).get("telegram_id")  # preserve if already linked
        }

    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)
    print("✅ Subscription database updated.")

def main():
    while True:
        try:
            print(f"\n🔄 Polling Gumroad API at {datetime.utcnow().isoformat()}...")
            subscribers = fetch_all_subscribers()
            update_subscriber_file(subscribers)
        except Exception as e:
            print(f"❌ Error during polling: {e}")
        time.sleep(3600)  # wait 1 hour

if __name__ == "__main__":
    main()
