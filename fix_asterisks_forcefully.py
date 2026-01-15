#!/usr/bin/env python3
"""
Force remove asterisks by:
1. Adding stronger prompt instruction
2. Post-processing AI responses to strip **text** → text
"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

changes = []

# 1. Add a function to strip asterisks from responses
strip_function = '''
# =============================================================================
# STRIP ASTERISKS FROM AI RESPONSES (Force clean formatting)
# =============================================================================
def strip_markdown_formatting(text: str) -> str:
    """Remove **bold** and *italic* markdown from text"""
    import re
    # Remove **bold** -> bold
    text = re.sub(r'\\*\\*([^*]+)\\*\\*', r'\\1', text)
    # Remove *italic* -> italic (but not inside words)
    text = re.sub(r'(?<![\\w])\\*([^*]+)\\*(?![\\w])', r'\\1', text)
    # Remove any remaining double asterisks
    text = text.replace('**', '')
    return text

'''

# Add after the generate_speech function or near the top
if 'def strip_markdown_formatting' not in content:
    # Find a good place - after the neural TTS section
    marker = '# =============================================================================\n# NEURAL TTS WRAPPER'
    if marker in content:
        content = content.replace(marker, strip_function + marker)
        changes.append("✓ Added strip_markdown_formatting function")
    else:
        # Try another location - before bot handlers
        marker2 = '@bot.message_handler(commands=["start"])'
        if marker2 in content:
            content = content.replace(marker2, strip_function + '\n' + marker2)
            changes.append("✓ Added strip_markdown_formatting function (alt location)")

# 2. Apply stripping to the main response output
# Find where full_reply is sent
old_send1 = 'bot.send_message(chat_id, f"🤖 Espaluz:\\n{full_reply}")'
new_send1 = 'bot.send_message(chat_id, f"🤖 Espaluz:\\n{strip_markdown_formatting(full_reply)}")'

if old_send1 in content:
    content = content.replace(old_send1, new_send1)
    changes.append("✓ Applied strip_markdown to main response #1")

# There might be multiple places
count = content.count(new_send1)
if count > 0:
    changes.append(f"   (Found {count} occurrences updated)")

# 3. Strengthen the system prompt instruction
old_instruction = '''⚠️ FORMATTING RULE: NEVER use asterisks (**text**) for bold - they appear as raw asterisks!
Instead, use EMOJIS for structure: ✅ ❌ 💡 🗣️ 📖 🌎 🎯
Keep text clean without Markdown symbols.'''

new_instruction = '''🚫🚫🚫 CRITICAL FORMATTING RULE - MUST FOLLOW 🚫🚫🚫
ABSOLUTELY NEVER use asterisks (**text** or *text*) anywhere in your response!
Asterisks appear as raw ** symbols to the user - this looks BROKEN!

INSTEAD of **bold text**, just write: bold text (no formatting)
Use EMOJIS for emphasis and structure:
✅ correct   ❌ wrong   💡 tip   🗣️ pronunciation   📖 vocabulary   🌎 culture   🎯 practice

Example of WRONG formatting: **"Hola"** means hello
Example of CORRECT formatting: ✅ "Hola" means hello

THIS IS MANDATORY. NO ASTERISKS ALLOWED.'''

if old_instruction in content:
    content = content.replace(old_instruction, new_instruction)
    changes.append("✓ Strengthened anti-asterisk instruction")

# Save
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Force Remove Asterisks Results:")
print("=" * 50)
for c in changes:
    print(c)
if not changes:
    print("No patterns found")
print("=" * 50)
