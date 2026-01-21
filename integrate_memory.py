#!/usr/bin/env python3
"""
Safe integration of espaluz_memory into main.py
Only ADDS code, never removes or modifies existing code.
"""

# Read the file
with open('main.py', 'r') as f:
    content = f.read()

# === PART 1: Add import after DATABASE MODULE ===
import_marker = '# =============================================================================\n# ONBOARDING SYSTEM (NEW - Jan 2026)'

import_code = '''# === UNIFIED MEMORY MODULE (NEW - Jan 2026) ===
# LangChain + PostgreSQL for cross-platform memory (Telegram + WhatsApp)
try:
    from espaluz_memory import EspaLuzMemory, LANGCHAIN_AVAILABLE
    UNIFIED_MEMORY_AVAILABLE = True
    print(f"✅ Unified memory loaded - LangChain: {LANGCHAIN_AVAILABLE}")
except ImportError as e:
    UNIFIED_MEMORY_AVAILABLE = False
    print(f"⚠️ Unified memory not available: {e}")

'''

if 'UNIFIED_MEMORY_AVAILABLE' not in content:
    content = content.replace(import_marker, import_code + import_marker)
    print('✅ Import block added')
else:
    print('⚠️ Import already exists, skipping')

# === PART 2: Add memory tracking in process_message_with_tracking ===
# Find the location after "Learning progress detected"
tracking_marker = '        print("📊 Learning progress detected")'

tracking_code = '''

    # === UNIFIED MEMORY TRACKING (NEW - Jan 2026) ===
    # Store conversation in unified database for cross-platform memory
    if UNIFIED_MEMORY_AVAILABLE:
        try:
            memory = EspaLuzMemory(platform='telegram', platform_user_id=user_id)
            memory.track_message()
            # Store conversation in LangChain memory
            if memory.chat_history:
                memory.chat_history.add_user_message(user_input)
                memory.chat_history.add_ai_message(full_reply)
            # Track vocabulary learned
            if learned_items.get("spanish_words"):
                for word in learned_items["spanish_words"][:5]:
                    try:
                        memory.add_vocabulary(word, word, "word")
                    except:
                        pass
            # Track emotional state
            emotion = session.get("context", {}).get("emotional_state", {}).get("current_emotion")
            if emotion:
                memory.track_emotion(emotion, user_input[:100])
            print(f"✅ Unified memory updated for {user_id}")
        except Exception as e:
            print(f"⚠️ Unified memory error (non-fatal): {e}")'''

if 'UNIFIED MEMORY TRACKING' not in content:
    content = content.replace(tracking_marker, tracking_marker + tracking_code)
    print('✅ Tracking block added')
else:
    print('⚠️ Tracking already exists, skipping')

# Write the file
with open('main.py', 'w') as f:
    f.write(content)

print('✅ Integration complete!')
