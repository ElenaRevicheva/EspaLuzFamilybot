import json

# Complete onboarding
onboarding = {
    "5481526862": {
        "step": "complete",
        "country": "costa_rica",
        "name": "Maria",
        "role": "parent"
    }
}
with open("user_onboarding.json", "w") as f:
    json.dump(onboarding, f, indent=2)

# Create session with Maria
sessions = {
    "5481526862": {
        "user_name": "Maria",
        "country": "costa_rica", 
        "role": "parent",
        "family_role": "elena",
        "onboarding_complete": True,
        "messages": []
    }
}
with open("user_sessions.json", "w") as f:
    json.dump(sessions, f, indent=2)

print("Onboarding and session restored for Maria!")
print(json.dumps(sessions, indent=2))