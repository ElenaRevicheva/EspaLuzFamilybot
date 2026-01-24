#!/usr/bin/env python3
"""
Safe integration of enhancements - ADDITIVE ONLY - v2
"""

def integrate():
    with open('/home/ubuntu/EspaLuzFamilybot/main.py', 'r') as f:
        content = f.read()
    
    # Check if already integrated
    if "ENHANCEMENTS_AVAILABLE" in content:
        print("⏭️ Enhancements already integrated")
        return
    
    # 1. Add import after unified memory import
    old_import = '''except ImportError as e:
    UNIFIED_MEMORY_AVAILABLE = False
    print(f"⚠️ Unified memory not available: {e}")

# =============================================================================
# ONBOARDING SYSTEM'''
    
    new_import = '''except ImportError as e:
    UNIFIED_MEMORY_AVAILABLE = False
    print(f"⚠️ Unified memory not available: {e}")

# === ENHANCEMENT MODULE (8 Features - Jan 2026) ===
try:
    from espaluz_enhancements import (
        build_enhanced_context,
        get_emotional_context_for_prompt,
        get_country_context_full,
        get_user_type_context,
        get_relocation_context,
        get_emergency_context,
        is_emergency_message,
        get_family_context,
        get_memory_context,
        COUNTRY_CONTEXTS_FULL
    )
    ENHANCEMENTS_AVAILABLE = True
    print("✅ Enhancement module loaded (all 21 countries + 8 features)!")
except ImportError as e:
    ENHANCEMENTS_AVAILABLE = False
    print(f"⚠️ Enhancements not available: {e}")

# =============================================================================
# ONBOARDING SYSTEM'''

    content = content.replace(old_import, new_import)
    print("✅ Added enhancement import")
    
    # 2. Find where system prompt is built and add enhancement context
    # Look for the end of the main system_content building
    old_system = '''        system_content += """
Provide nuanced language help with natural conversation, idioms, and practical vocabulary.
"""'''
    
    new_system = '''        system_content += """
Provide nuanced language help with natural conversation, idioms, and practical vocabulary.
"""
        
        # === ENHANCEMENT CONTEXT (8 Features - All 21 Countries) ===
        if ENHANCEMENTS_AVAILABLE and UNIFIED_MEMORY_AVAILABLE:
            try:
                # Build enhanced context from database
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
                    print(f"✅ Enhanced context: country={user_country}, type={user_type_val}")
            except Exception as e:
                print(f"⚠️ Enhancement error: {e}")'''

    if "ENHANCEMENT CONTEXT (8 Features" not in content:
        content = content.replace(old_system, new_system)
        print("✅ Added enhancement context injection")
    else:
        print("⏭️ Enhancement context already exists")
    
    # Write back
    with open('/home/ubuntu/EspaLuzFamilybot/main.py', 'w') as f:
        f.write(content)
    
    print("\n✅ Integration v2 complete!")

if __name__ == "__main__":
    integrate()
