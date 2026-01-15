#!/usr/bin/env python3
"""
Comprehensive emoji fix:
1. Better emoji stripping from video script (ALL emojis)
2. Encourage more emojis in text responses
"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

changes = []

# 1. Create a comprehensive emoji removal function
emoji_function = '''
def strip_emojis(text: str) -> str:
    """Remove ALL emojis from text (for TTS so they're not pronounced)"""
    import re
    # Comprehensive emoji pattern covering all Unicode emoji ranges
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed characters
        "\U0001F1E0-\U0001F1FF"  # Flags
        "\U00002600-\U000026FF"  # Misc symbols (sun, stars, etc)
        "\U00002700-\U000027BF"  # Dingbats
        "\U0000FE00-\U0000FE0F"  # Variation Selectors
        "\U0001F000-\U0001F02F"  # Mahjong
        "\U0001F0A0-\U0001F0FF"  # Playing cards
        "✅❌💡🗣️📖🌎🎯☕🎓🏖️"  # Common ones we use
        "]+"
    , re.UNICODE)
    return emoji_pattern.sub('', text).strip()

'''

# Add the function if not exists
if 'def strip_emojis(' not in content:
    # Add near the strip_markdown_formatting function
    marker = 'def strip_markdown_formatting'
    if marker in content:
        idx = content.find(marker)
        content = content[:idx] + emoji_function + '\n' + content[idx:]
        changes.append("✓ Added comprehensive strip_emojis function")

# 2. Update the video script extraction to use the new function
old_emoji_strip = '''            # Remove emojis from video script (so they're not pronounced)
            import re
            script = re.sub(r'[\\U0001F300-\\U0001F9FF]|[\\U00002600-\\U000027BF]|[\\U0001F600-\\U0001F64F]', '', script)
            script = script.strip()'''

new_emoji_strip = '''            # Remove ALL emojis from video script (so they're not pronounced)
            script = strip_emojis(script)'''

if old_emoji_strip in content:
    content = content.replace(old_emoji_strip, new_emoji_strip)
    changes.append("✓ Updated video script to use strip_emojis")

# 3. Also strip emojis from the TTS text in fast_tts_for_video
old_tts_text = '''        # For video audio, we want a concise version
        words = text.split()
        if len(words) > 150:
            text = ' '.join(words[:150])

        # Generate TTS'''

new_tts_text = '''        # Strip emojis so they're not pronounced
        text = strip_emojis(text)
        
        # For video audio, we want a concise version
        words = text.split()
        if len(words) > 150:
            text = ' '.join(words[:150])

        # Generate TTS'''

if old_tts_text in content:
    content = content.replace(old_tts_text, new_tts_text)
    changes.append("✓ Added emoji stripping to fast_tts_for_video")

# 4. Update the prompt to encourage MORE emojis in text (but not video)
old_emoji_instruction = '''Use EMOJIS for emphasis and structure:
✅ correct   ❌ wrong   💡 tip   🗣️ pronunciation   📖 vocabulary   🌎 culture   🎯 practice'''

new_emoji_instruction = '''Use EMOJIS GENEROUSLY for structure and visual appeal:
✅ for correct answers and confirmations
❌ for errors to avoid  
💡 for tips and suggestions
🗣️ for pronunciation guidance
📖 for vocabulary sections
🌎 for cultural notes
🎯 for practice suggestions
☕ 🍽️ 🏖️ 🏫 🏥 🏦 for topics (coffee, food, beach, school, hospital, bank)
🎓 for learning achievements

Use emojis to START each section header - makes the response scannable and friendly!
Example: "🏫 Top bilingual schools:" not just "Top bilingual schools:"'''

if old_emoji_instruction in content:
    content = content.replace(old_emoji_instruction, new_emoji_instruction)
    changes.append("✓ Updated prompt to encourage more emojis")

# 5. Also check the secondary prompt location
old_format2 = '''📝 FORMATTING RULES:
- NEVER use **asterisks** for bold - they show raw!
- Use emojis for structure: ✅ ❌ 💡 🗣️ 📖 🌎'''

new_format2 = '''📝 FORMATTING RULES:
- NEVER use **asterisks** for bold - they show raw!
- Use EMOJIS GENEROUSLY: ✅ ❌ 💡 🗣️ 📖 🌎 🎯 ☕ 🍽️ 🏖️ 🏫 🏥 🏦 🎓
- Start each section with a relevant emoji
- Emojis will be stripped from video script automatically'''

if old_format2 in content:
    content = content.replace(old_format2, new_format2)
    changes.append("✓ Updated secondary format instruction")

# Save
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Comprehensive Emoji Fix Results:")
print("=" * 50)
for c in changes:
    print(c)
if not changes:
    print("No patterns found")
print("=" * 50)
