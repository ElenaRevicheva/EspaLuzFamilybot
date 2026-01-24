#!/usr/bin/env python3
"""Add enhancement context injection - correct version"""

with open('/home/ubuntu/EspaLuzFamilybot/main.py', 'r') as f:
    content = f.read()

if "ENHANCEMENT CONTEXT (8 Features" in content:
    print("⏭️ Already integrated")
    exit(0)

# Find the correct insertion point
old_text = '''        system_content += """
Provide nuanced language assistance focused on natural conversation, idioms, and practical vocabulary.
"""

    # =========================================================================
    # 🧠 ENHANCED EMOTIONAL INTELLIGENCE INTEGRATION'''

new_text = '''        system_content += """
Provide nuanced language assistance focused on natural conversation, idioms, and practical vocabulary.
"""
        
        # === ENHANCEMENT CONTEXT (8 Features - All 21 Countries) ===
        if ENHANCEMENTS_AVAILABLE and UNIFIED_MEMORY_AVAILABLE:
            try:
                user_country = session["context"]["user"]["preferences"].get("country", "panama")
                user_type_val = session["context"]["user"]["preferences"].get("user_type", "expat")
                learning_dir = session["context"]["user"]["preferences"].get("learning_direction", "spanish")
                
                enhancement_ctx = build_enhanced_context(
                    memory_instance=memory,
                    user_type=user_type_val,
                    country=user_country,
                    learning_direction=learning_dir,
                    current_message=new_message
                )
                
                if enhancement_ctx:
                    system_content += f"\\n{enhancement_ctx}\\n"
                    print(f"✅ Enhanced: country={user_country}, type={user_type_val}")
            except Exception as e:
                print(f"⚠️ Enhancement error: {e}")

    # =========================================================================
    # 🧠 ENHANCED EMOTIONAL INTELLIGENCE INTEGRATION'''

content = content.replace(old_text, new_text)

with open('/home/ubuntu/EspaLuzFamilybot/main.py', 'w') as f:
    f.write(content)

print("✅ Enhancement context added!")
