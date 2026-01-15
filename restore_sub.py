import json
discovered = {"I-4JF9MBXLXM51": {"email": "marinakulaginabowen@gmail.com", "status": "ACTIVE", "discovered_at": "2026-01-13"}}
with open("discovered_subscriptions.json", "w") as f:
    json.dump(discovered, f, indent=2)
print("Created discovered_subscriptions.json")
try:
    with open("subscribers.json", "r") as f:
        subs = json.load(f)
except:
    subs = {}
subs["marinakulaginabowen@gmail.com"] = {"subscriber_id": "I-4JF9MBXLXM51", "status": "active", "last_checked": "2026-01-15", "telegram_id": None, "source": "paypal"}
with open("subscribers.json", "w") as f:
    json.dump(subs, f, indent=2)
print("Updated subscribers.json")