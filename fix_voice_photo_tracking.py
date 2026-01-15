#!/usr/bin/env python3
"""Fix database tracking for voice and photo handlers"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# Fix voice handler - add track_user
old_voice = '''    # === DATABASE TRACKING (NEW) ===
    if DATABASE_AVAILABLE and db:
        try:
            db.track_message(user_id, 'voice')
        except:
            pass'''

new_voice = '''    # === DATABASE TRACKING ===
    if DATABASE_AVAILABLE and db:
        try:
            username = message.from_user.username if message.from_user else None
            first_name = message.from_user.first_name if message.from_user else None
            db.track_user(user_id, username=username, first_name=first_name)
            db.track_message(user_id, 'voice')
            print(f"DB: Tracked voice from {user_id}", flush=True)
        except Exception as e:
            print(f"DB voice tracking error: {e}", flush=True)'''

if old_voice in content:
    content = content.replace(old_voice, new_voice)
    changes += 1
    print('Fixed voice handler tracking')

# Now check photo handler and add tracking if needed
# First, let's see if photo already has tracking
if '@bot.message_handler(content_types=["photo"])' in content:
    # Find photo handler
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '@bot.message_handler(content_types=["photo"])' in line and 'def handle_photo' in lines[i+1]:
            # Check if DATABASE tracking exists within next 20 lines
            has_db_tracking = False
            for j in range(i, min(i+25, len(lines))):
                if 'DATABASE_AVAILABLE' in lines[j] and 'db.track' in content[content.find(lines[j]):content.find(lines[j])+200]:
                    has_db_tracking = True
                    break
            
            if not has_db_tracking:
                print(f'Photo handler at line {i+1} needs tracking')
            else:
                print(f'Photo handler at line {i+1} already has tracking')
            break

if changes > 0:
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'SUCCESS: Made {changes} changes')
else:
    print('No changes needed or patterns not found')
