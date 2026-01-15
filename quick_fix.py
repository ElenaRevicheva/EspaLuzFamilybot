import json
# Clear sessions - let bot recreate properly
with open("user_sessions.json", "w") as f:
    json.dump({}, f)
# Mark onboarding complete
onboarding = {"5481526862": {"step": "complete", "country": "costa_rica", "name": "Maria", "role": "parent"}}
with open("user_onboarding.json", "w") as f:
    json.dump(onboarding, f, indent=2)
print("Fixed! Sessions cleared, onboarding marked complete")