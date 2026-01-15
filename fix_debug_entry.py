#!/usr/bin/env python3
"""Add debug print at the very start of handle_text"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_handler = '''@bot.message_handler(content_types=["text"])
def handle_text(message):
    user_id = str(message.from_user.id)
    text = message.text.strip()
    
    # === DATABASE TRACKING (first thing!) ==='''

new_handler = '''@bot.message_handler(content_types=["text"])
def handle_text(message):
    print(f">>> HANDLE_TEXT ENTERED: {message.from_user.id} - {message.text[:30] if message.text else 'None'}", flush=True)
    user_id = str(message.from_user.id)
    text = message.text.strip()
    
    # === DATABASE TRACKING (first thing!) ==='''

if old_handler in content:
    content = content.replace(old_handler, new_handler)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: Added debug print at handler entry')
else:
    print('ERROR: Pattern not found')
