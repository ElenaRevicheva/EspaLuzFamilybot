#!/usr/bin/env python3
"""Fix database tracking in main.py - add tracking at TOP of message handler"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the text handler and add DB tracking right after user_id line
old_pattern = '''@bot.message_handler(content_types=["text"])
def handle_text(message):
    user_id = str(message.from_user.id)
    text = message.text.strip()
    
    # Track activity for analytics'''

new_code = '''@bot.message_handler(content_types=["text"])
def handle_text(message):
    user_id = str(message.from_user.id)
    text = message.text.strip()
    
    # === DATABASE TRACKING (first thing!) ===
    if DATABASE_AVAILABLE and db:
        try:
            username = message.from_user.username if message.from_user else None
            first_name = message.from_user.first_name if message.from_user else None
            db.track_user(user_id, username=username, first_name=first_name)
            db.track_message(user_id, 'text')
            print(f"DB: Tracked text from {user_id}", flush=True)
        except Exception as e:
            print(f"DB tracking error: {e}", flush=True)
    
    # Track activity for analytics'''

if old_pattern in content:
    content = content.replace(old_pattern, new_code)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: Added DB tracking to text handler')
else:
    print('ERROR: Pattern not found')
    # Show what we're looking for
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'def handle_text' in line:
            print(f"Found at line {i+1}: {line}")
            for j in range(i, min(i+10, len(lines))):
                print(f"  {j+1}: {lines[j]}")
