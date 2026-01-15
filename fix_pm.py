import re

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the pattern in process_message (the other function)
old_code = '''    if user_id not in user_sessions:
        user_sessions[user_id] = create_initial_session(user_id, message_obj.from_user, message_obj.chat, user_input)
    
    session = user_sessions[user_id]
    session["context"]["conversation"]["message_count"] += 1'''

new_code = '''    if user_id not in user_sessions:
        user_sessions[user_id] = create_initial_session(user_id, message_obj.from_user, message_obj.chat, user_input)
        # IMPORTANT: Load onboarding data into new session!
        onboarding = get_user_onboarding(user_id)
        if onboarding.get("step") == "complete":
            prefs = user_sessions[user_id]["context"]["user"]["preferences"]
            prefs["country"] = onboarding.get("country", "panama")
            prefs["user_name"] = onboarding.get("name", "Friend")
            prefs["family_role"] = onboarding.get("role", "learner")
            print(f"Loaded onboarding for {prefs['user_name']} in {prefs['country']}")
    
    session = user_sessions[user_id]
    session["context"]["conversation"]["message_count"] += 1'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Fixed process_message too!")
else:
    print("Pattern not found in process_message (may already be fixed or different)")