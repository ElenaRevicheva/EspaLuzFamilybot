#!/usr/bin/env python3
"""
Remove asterisks from AI responses and use emojis instead.
Also ensure VIDEO SCRIPT section doesn't include emojis (for clean pronunciation).
"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

changes = []

# 1. Find the main formatting instruction area and add no-asterisks rule
# Look for the response format section

old_format_instruction = '''2️⃣ A second short block inside [VIDEO SCRIPT START] ... [VIDEO SCRIPT END] for video:
       - Must be 2 to 4 concise sentences MAX
       - Use both Spanish and English
       - ALWAYS use the user's ACTUAL NAME (not Elena!)
       - Tone: warm, clear, and simple for spoken delivery
       - It will be spoken by an avatar on video, so make it suitable for audio (not robotic or boring!)'''

new_format_instruction = '''2️⃣ A second short block inside [VIDEO SCRIPT START] ... [VIDEO SCRIPT END] for video:
       - Must be 2 to 4 concise sentences MAX
       - Use both Spanish and English
       - ALWAYS use the user's ACTUAL NAME (not Elena!)
       - Tone: warm, clear, and simple for spoken delivery
       - It will be spoken by an avatar on video, so make it suitable for audio (not robotic or boring!)
       - NO EMOJIS in the video script section (they will be pronounced!)
       
📝 CRITICAL FORMATTING RULES:
   - NEVER use asterisks (**bold**) for emphasis - they show as raw asterisks!
   - Use EMOJIS to structure your response instead:
     ✅ for correct answers
     ❌ for errors to fix
     💡 for tips
     🗣️ for pronunciation
     📖 for vocabulary
     🌎 for cultural notes
     🎯 for practice suggestions
   - Keep formatting clean and readable
   - Use line breaks and spacing for structure'''

if old_format_instruction in content:
    content = content.replace(old_format_instruction, new_format_instruction)
    changes.append("✓ Added no-asterisks formatting rules")

# 2. Add additional instruction near the beginning of system_content
old_system_start = '''system_content = "You are Espaluz, a bilingual emotionally intelligent AI language tutor for a Russian expat family in Panama."'''

new_system_start = '''system_content = """You are Espaluz, a bilingual emotionally intelligent AI language tutor.

⚠️ FORMATTING RULE: NEVER use asterisks (**text**) for bold - they appear as raw asterisks!
Instead, use EMOJIS for structure: ✅ ❌ 💡 🗣️ 📖 🌎 🎯
Keep text clean without Markdown symbols.
"""'''

if old_system_start in content:
    content = content.replace(old_system_start, new_system_start)
    changes.append("✓ Updated main system content start")

# 3. Also update the second system prompt (for image OCR / different path)
# Find the other response format instruction
old_format2 = '''2️⃣ Then add a short second section inside [VIDEO SCRIPT START] and [VIDEO SCRIPT END], like:

[VIDEO SCRIPT START]
¡Hola! Hoy vamos a aprender algo nuevo.
Hello! Today we will learn something new.
[VIDEO SCRIPT END]

This second block will be spoken in video, so keep it short, warm, and clear.'''

new_format2 = '''2️⃣ Then add a short second section inside [VIDEO SCRIPT START] and [VIDEO SCRIPT END], like:

[VIDEO SCRIPT START]
Hola! Hoy vamos a aprender algo nuevo.
Hello! Today we will learn something new.
[VIDEO SCRIPT END]

This second block will be spoken in video, so keep it short, warm, and clear.
NO emojis in the video script - they will be pronounced!

📝 FORMATTING RULES:
- NEVER use **asterisks** for bold - they show raw!
- Use emojis for structure: ✅ ❌ 💡 🗣️ 📖 🌎'''

if old_format2 in content:
    content = content.replace(old_format2, new_format2)
    changes.append("✓ Updated secondary format instruction")

# 4. Add emoji-stripping to the video script extraction
old_script_extract = '''if start_index < end_index:
            script = full_response[start_index:end_index].strip()'''

new_script_extract = '''if start_index < end_index:
            script = full_response[start_index:end_index].strip()
            # Remove emojis from video script (so they're not pronounced)
            import re
            script = re.sub(r'[\\U0001F300-\\U0001F9FF]|[\\U00002600-\\U000027BF]|[\\U0001F600-\\U0001F64F]', '', script)
            script = script.strip()'''

if old_script_extract in content:
    content = content.replace(old_script_extract, new_script_extract)
    changes.append("✓ Added emoji stripping from video script")

# Save
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Remove Asterisks Results:")
print("=" * 40)
for c in changes:
    print(c)
if not changes:
    print("No patterns found - may need manual update")
print("=" * 40)
