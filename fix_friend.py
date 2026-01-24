#!/usr/bin/env python3
"""Remove 'friend' fallback from all locations"""

with open('/home/ubuntu/EspaLuzFamilybot/main.py', 'r') as f:
    content = f.read()

# Count occurrences
count_before = content.count('"friend"')
print(f"Found {count_before} occurrences of 'friend' fallback")

# Replace the problematic fallbacks
# Line 1483: .get("user_name", "friend") -> .get("user_name")  
content = content.replace(
    '.get("user_name", "friend")',
    '.get("user_name")'
)

# Line 1688: .get("first_name", "friend") -> .get("first_name")
content = content.replace(
    '.get("first_name", "friend")',
    '.get("first_name")'
)

count_after = content.count('"friend"')
print(f"After fix: {count_after} occurrences remain (non-fallback uses)")

with open('/home/ubuntu/EspaLuzFamilybot/main.py', 'w') as f:
    f.write(content)

print("✅ Fixed!")
