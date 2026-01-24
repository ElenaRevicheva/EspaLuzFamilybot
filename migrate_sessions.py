#!/usr/bin/env python3
"""Migrate existing sessions to include onboarding data (name, country)"""

import json

# Load sessions
with open('/home/ubuntu/EspaLuzFamilybot/user_sessions.json', 'r') as f:
    sessions = json.load(f)

# Load onboarding
with open('/home/ubuntu/EspaLuzFamilybot/user_onboarding.json', 'r') as f:
    onboarding = json.load(f)

# Update sessions with onboarding data
for user_id, session in sessions.items():
    if user_id in onboarding and onboarding[user_id].get('step') == 'complete':
        prefs = session.get('context', {}).get('user', {}).get('preferences', {})
        prefs['user_name'] = onboarding[user_id].get('name')
        prefs['country'] = onboarding[user_id].get('country')
        print(f"Updated {user_id}: name={prefs.get('user_name')}, country={prefs.get('country')}")

# Save back
with open('/home/ubuntu/EspaLuzFamilybot/user_sessions.json', 'w') as f:
    json.dump(sessions, f, indent=2)

print("✅ Sessions migrated!")
