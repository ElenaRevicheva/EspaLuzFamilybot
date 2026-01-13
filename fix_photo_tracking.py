#!/usr/bin/env python3
"""Fix database tracking for photo handler"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_photo = '''@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    """Handle photo message with text recognition and explanation for Telegram"""
    try:
        user_id = str(message.from_user.id)
        print(f"[INFO] Received photo from user {user_id} at {message.date}", flush=True)'''

new_photo = '''@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    """Handle photo message with text recognition and explanation for Telegram"""
    try:
        user_id = str(message.from_user.id)
        print(f"[INFO] Received photo from user {user_id} at {message.date}", flush=True)
        
        # === DATABASE TRACKING ===
        if DATABASE_AVAILABLE and db:
            try:
                username = message.from_user.username if message.from_user else None
                first_name = message.from_user.first_name if message.from_user else None
                db.track_user(user_id, username=username, first_name=first_name)
                db.track_message(user_id, 'image')
                print(f"DB: Tracked photo from {user_id}", flush=True)
            except Exception as e:
                print(f"DB photo tracking error: {e}", flush=True)'''

if old_photo in content:
    content = content.replace(old_photo, new_photo)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: Added DB tracking to photo handler')
else:
    print('ERROR: Pattern not found')
