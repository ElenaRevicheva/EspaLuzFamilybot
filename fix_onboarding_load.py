import re

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the pattern where session is created in process_message_with_tracking
old_code = '''    # Init session
    if user_id not in user_sessions:
        user_sessions[user_id] = create_initial_session(user_id, message_obj.from_user, message_obj.chat, user_input)
        print(f"Created new session for user {user_id}")

    session = user_sessions[user_id]'''

new_code = '''    # Init session
    if user_id not in user_sessions:
        user_sessions[user_id] = create_initial_session(user_id, message_obj.from_user, message_obj.chat, user_input)
        print(f"Created new session for user {user_id}")
        # IMPORTANT: Load onboarding data into new session!
        onboarding = get_user_onboarding(user_id)
        if onboarding.get("step") == "complete":
            prefs = user_sessions[user_id]["context"]["user"]["preferences"]
            prefs["country"] = onboarding.get("country", "panama")
            prefs["user_name"] = onboarding.get("name", "Friend")
            prefs["family_role"] = onboarding.get("role", "learner")
            print(f"Loaded onboarding for {prefs['user_name']} in {prefs['country']}")

    session = user_sessions[user_id]'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Added onboarding data loading to process_message_with_tracking")
else:
    print("ERROR: Pattern not found - checking...")
    # Show what we have around line 3094
    lines = content.split('\n')
    for i, line in enumerate(lines[3090:3105], start=3091):
        print(f"{i}: {line}")