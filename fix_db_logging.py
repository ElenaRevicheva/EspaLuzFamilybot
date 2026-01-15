#!/usr/bin/env python3
"""Add logging to database convenience functions"""

with open('espaluz_database.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_convenience = '''# Convenience functions
def track_user(user_id: str, **kwargs) -> bool:
    return db.track_user(user_id, **kwargs)

def track_message(user_id: str, message_type: str = 'text') -> bool:
    return db.track_message(user_id, message_type)'''

new_convenience = '''# Convenience functions
def track_user(user_id: str, **kwargs) -> bool:
    print(f"[DB MODULE] track_user called for {user_id}, use_database={db.use_database}", flush=True)
    result = db.track_user(user_id, **kwargs)
    print(f"[DB MODULE] track_user result: {result}", flush=True)
    return result

def track_message(user_id: str, message_type: str = 'text') -> bool:
    print(f"[DB MODULE] track_message called for {user_id}, type={message_type}", flush=True)
    result = db.track_message(user_id, message_type)
    print(f"[DB MODULE] track_message result: {result}", flush=True)
    return result'''

if old_convenience in content:
    content = content.replace(old_convenience, new_convenience)
    with open('espaluz_database.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: Added logging to database convenience functions')
else:
    print('ERROR: Pattern not found')
    # Try to find what's there
    if 'def track_user' in content:
        idx = content.find('def track_user')
        print(f'Found track_user at position {idx}:')
        print(content[idx:idx+300])
