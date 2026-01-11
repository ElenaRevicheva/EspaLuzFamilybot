#!/usr/bin/env python3
"""Fix ALL indentation issues in main.py"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern 1: Fix "if translated:" blocks
# Looking for pattern where "if translated:" is followed by unindented bot.send_message
import re

# Fix pattern: "    if translated:\n    bot.send_message" -> "    if translated:\n        bot.send_message"
content = re.sub(
    r'(    if translated:\n)(    )(bot\.send_message)',
    r'\1        \3',
    content
)

# Fix pattern: "    bot.send_message(...)\n    print" -> keep both properly indented  
content = re.sub(
    r'(        bot\.send_message[^\n]+\n)(    )(print\("Translation sent"\))',
    r'\1        \3',
    content
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed patterns!")

# Now verify
import py_compile
try:
    py_compile.compile('main.py', doraise=True)
    print("✅ Syntax is valid!")
except py_compile.PyCompileError as e:
    print(f"❌ Syntax error: {e}")
