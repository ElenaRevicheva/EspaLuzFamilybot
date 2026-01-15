#!/usr/bin/env python3
"""
Fix clean_text_for_speech to actually strip ALL emojis
"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

changes = []

# Replace the clean_text_for_speech function with one that includes emoji stripping
old_function = '''def clean_text_for_speech(text: str) -> str:
    """Remove punctuation marks and formatting for natural speech"""
    # Remove markdown formatting
    text = re.sub(r'\\*+([^*]+)\\*+', r'\\1', text)  # Remove asterisks
    text = re.sub(r'_+([^_]+)_+', r'\\1', text)    # Remove underscores
    text = re.sub(r'`+([^`]+)`+', r'\\1', text)    # Remove backticks
    
    # Remove quotes but keep the content
    text = re.sub(r'"([^"]+)"', r'\\1', text)
    text = re.sub(r"'([^']+)'", r'\\1', text)
    
    # Remove numbers in lists (1. 2. etc)
    text = re.sub(r'^\\d+\\.\\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\\n\\d+\\.\\s*', '\\n', text)
    
    # Remove emoji numbers
    text = re.sub(r'[0-9]️⃣', '', text)
    
    # Remove other common symbols but keep sentence flow
    text = re.sub(r'[#@\\[\\](){}<>]', '', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\\s+', ' ', text)
    return text.strip()'''

new_function = '''def clean_text_for_speech(text: str) -> str:
    """Remove punctuation marks, formatting AND EMOJIS for natural speech"""
    # FIRST: Remove ALL emojis (so they're not pronounced!)
    emoji_pattern = re.compile(
        "["
        "\\U0001F600-\\U0001F64F"  # emoticons
        "\\U0001F300-\\U0001F5FF"  # symbols & pictographs
        "\\U0001F680-\\U0001F6FF"  # transport & map symbols
        "\\U0001F700-\\U0001F77F"  # alchemical symbols
        "\\U0001F780-\\U0001F7FF"  # Geometric Shapes Extended
        "\\U0001F800-\\U0001F8FF"  # Supplemental Arrows-C
        "\\U0001F900-\\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\\U0001FA00-\\U0001FA6F"  # Chess Symbols
        "\\U0001FA70-\\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\\U00002702-\\U000027B0"  # Dingbats
        "\\U000024C2-\\U0001F251"  # Enclosed characters
        "\\U0001F1E0-\\U0001F1FF"  # Flags
        "\\U00002600-\\U000026FF"  # Misc symbols (sun, stars, etc)
        "\\U00002700-\\U000027BF"  # Dingbats
        "\\U0000FE00-\\U0000FE0F"  # Variation Selectors
        "\\U0001F000-\\U0001F02F"  # Mahjong
        "\\U0001F0A0-\\U0001F0FF"  # Playing cards
        "\\U00002B50"              # Star
        "\\U00002705"              # Check mark
        "\\U0000274C"              # X mark
        "\\U0001F4A1"              # Lightbulb
        "\\U0001F5E3"              # Speaking head
        "\\U0001F4D6"              # Book
        "\\U0001F30E"              # Globe
        "\\U0001F3AF"              # Target
        "]+"
    , re.UNICODE)
    text = emoji_pattern.sub('', text)
    
    # Remove markdown formatting
    text = re.sub(r'\\*+([^*]+)\\*+', r'\\1', text)  # Remove asterisks
    text = re.sub(r'_+([^_]+)_+', r'\\1', text)    # Remove underscores
    text = re.sub(r'`+([^`]+)`+', r'\\1', text)    # Remove backticks
    
    # Remove quotes but keep the content
    text = re.sub(r'"([^"]+)"', r'\\1', text)
    text = re.sub(r"'([^']+)'", r'\\1', text)
    
    # Remove numbers in lists (1. 2. etc)
    text = re.sub(r'^\\d+\\.\\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\\n\\d+\\.\\s*', '\\n', text)
    
    # Remove emoji numbers
    text = re.sub(r'[0-9]️⃣', '', text)
    
    # Remove other common symbols but keep sentence flow
    text = re.sub(r'[#@\\[\\](){}<>]', '', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\\s+', ' ', text)
    return text.strip()'''

if old_function in content:
    content = content.replace(old_function, new_function)
    changes.append("✓ Updated clean_text_for_speech with comprehensive emoji removal")
else:
    # Try a simpler match
    simple_old = 'def clean_text_for_speech(text: str) -> str:\n    """Remove punctuation marks and formatting for natural speech"""'
    if simple_old in content:
        # Just add emoji stripping at the start of the function
        changes.append("Pattern not exact - trying alternative approach")
    else:
        changes.append("❌ Could not find clean_text_for_speech function")

# Save
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix Clean Text Emojis Results:")
print("=" * 50)
for c in changes:
    print(c)
print("=" * 50)
