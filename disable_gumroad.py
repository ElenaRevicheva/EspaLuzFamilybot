#!/usr/bin/env python3
"""Disable Gumroad polling"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_gumroad = '''def poll_subscriptions():
    """Poll Gumroad API and update local subscriber list"""
    try:'''

new_gumroad = '''def poll_subscriptions():
    """Poll Gumroad API and update local subscriber list"""
    # DISABLED: Gumroad is suspended - Jan 2026
    print("⏸️ Gumroad polling DISABLED (suspended)")
    return
    try:'''

if old_gumroad in content:
    content = content.replace(old_gumroad, new_gumroad)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Disabled Gumroad poll_subscriptions")
else:
    print("⚠️ Pattern not found - checking if already disabled")
    if "Gumroad polling DISABLED" in content:
        print("✅ Already disabled")
    else:
        # Show what's there
        idx = content.find('def poll_subscriptions')
        if idx > 0:
            print(f"Found at position {idx}:")
            print(content[idx:idx+200])
