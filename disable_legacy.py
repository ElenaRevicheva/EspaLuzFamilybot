#!/usr/bin/env python3
"""Disable legacy Gumroad and Supabase systems"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# 1. Disable Gumroad polling by adding early return
old_gumroad = '''def poll_gumroad_subscribers():
    """Poll Gumroad API and update local subscriber list"""'''

new_gumroad = '''def poll_gumroad_subscribers():
    """Poll Gumroad API and update local subscriber list"""
    # DISABLED: Gumroad is suspended - Jan 2026
    print("⏸️ Gumroad polling DISABLED (suspended)")
    return'''

if old_gumroad in content:
    content = content.replace(old_gumroad, new_gumroad)
    changes += 1
    print("✅ Disabled Gumroad polling")

# 2. Disable Supabase tracking function
old_supabase = '''def track_telegram_conversation'''

# Find and disable the Supabase tracking
if 'def track_telegram_conversation' in content:
    # Find the function and add early return
    idx = content.find('def track_telegram_conversation')
    if idx > 0:
        # Find the docstring end
        docstring_start = content.find('"""', idx)
        docstring_end = content.find('"""', docstring_start + 3) + 3
        # Insert early return after docstring
        old_func_start = content[idx:docstring_end]
        new_func_start = old_func_start + "\n    # DISABLED: Using PostgreSQL now - Jan 2026\n    return"
        content = content[:idx] + new_func_start + content[docstring_end:]
        changes += 1
        print("✅ Disabled Supabase track_telegram_conversation")

# 3. Disable post_progress_to_supabase
old_post = '''def post_progress_to_supabase(user_id, payload):
    try:
        print(f"📡 Sending progress data to Supabase for user {user_id}...")'''

new_post = '''def post_progress_to_supabase(user_id, payload):
    # DISABLED: Using PostgreSQL now - Jan 2026
    return
    try:
        print(f"📡 Sending progress data to Supabase for user {user_id}...")'''

if old_post in content:
    content = content.replace(old_post, new_post)
    changes += 1
    print("✅ Disabled post_progress_to_supabase")

if changes > 0:
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n✅ SUCCESS: Made {changes} changes to disable legacy systems")
else:
    print("⚠️ No changes made - patterns not found or already disabled")
