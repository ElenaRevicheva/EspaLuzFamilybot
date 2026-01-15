#!/usr/bin/env python3
"""
Remove legacy Gumroad and Supabase code from main.py
PostgreSQL is now the primary database.
"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

changes = []

# 1. Remove Supabase tracking function call in process_message_with_tracking
old_supabase_tracking = '''    # 🆕 NEW: Track this conversation in Supabase
    try:
        track_telegram_conversation(user_id, user_input, full_reply, session)
    except Exception as e:
        print(f"⚠️ Supabase tracking failed (non-critical): {e}")'''

if old_supabase_tracking in content:
    content = content.replace(old_supabase_tracking, '    # Supabase tracking removed - using PostgreSQL now')
    changes.append('Removed Supabase tracking call')

# 2. Remove "tracked in Supabase" print
old_supabase_print = 'print("📊 Learning progress detected - tracked in Supabase")'
new_supabase_print = 'print("📊 Learning progress detected")'
if old_supabase_print in content:
    content = content.replace(old_supabase_print, new_supabase_print)
    changes.append('Updated learning progress message')

# 3. Update function docstring
old_docstring = '"""Enhanced version of process_message with Supabase tracking"""'
new_docstring = '"""Enhanced version of process_message with PostgreSQL tracking"""'
if old_docstring in content:
    content = content.replace(old_docstring, new_docstring)
    changes.append('Updated function docstring')

# 4. Remove Gumroad polling call in bot runtime
old_gumroad_runtime = '''            print(f"\\n🔄 Polling Gumroad API inside bot runtime...")
            poll_gumroad_subscribers()'''
new_gumroad_runtime = '''            # Gumroad polling removed - using PayPal now
            pass'''
if old_gumroad_runtime in content:
    content = content.replace(old_gumroad_runtime, new_gumroad_runtime)
    changes.append('Removed Gumroad runtime polling')

# 5. Disable the poll_gumroad_subscribers function body (keep function for safety)
old_poll_func_start = '''def poll_gumroad_subscribers():
    """Poll Gumroad API and update local subscriber list"""
    # DISABLED: Gumroad is suspended - Jan 2026
    print("⏸️ Gumroad polling DISABLED (suspended)")
    return'''

if old_poll_func_start in content:
    # Already disabled, just update the message
    new_poll_func_start = '''def poll_gumroad_subscribers():
    """DEPRECATED: Gumroad suspended. Using PayPal now."""
    return  # Function disabled'''
    content = content.replace(old_poll_func_start, new_poll_func_start)
    changes.append('Updated poll_gumroad_subscribers to deprecated')

# 6. Comment out post_progress_to_supabase calls
old_post_call = 'post_progress_to_supabase(user_id, progress_payload)'
new_post_call = '# post_progress_to_supabase(user_id, progress_payload)  # Disabled - using PostgreSQL'
if old_post_call in content:
    content = content.replace(old_post_call, new_post_call)
    changes.append('Disabled post_progress_to_supabase call')

# 7. Update Supabase key debug print
old_debug = 'print("🔐 Supabase key present:", os.environ.get(\'SUPABASE_ANON_KEY\') is not None)'
new_debug = '# Supabase key check removed - using PostgreSQL'
if old_debug in content:
    content = content.replace(old_debug, new_debug)
    changes.append('Removed Supabase key debug')

if changes:
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"SUCCESS: Made {len(changes)} changes:")
    for c in changes:
        print(f"  ✓ {c}")
else:
    print("No changes needed - legacy code may already be removed")
