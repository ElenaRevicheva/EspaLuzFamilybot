#!/usr/bin/env python3
"""
Safe integration of enhancements - ADDITIVE ONLY
This script adds the enhancement import and call without changing existing code.
"""

def integrate():
    with open('/home/ubuntu/EspaLuzFamilybot/main.py', 'r') as f:
        content = f.read()
    
    # Check if already integrated
    if "espaluz_enhancements" in content:
        print("⏭️ Enhancements already integrated")
        return
    
    # 1. Add import after existing imports
    import_marker = "PERSONALIZATION_AVAILABLE = False"
    new_import = """PERSONALIZATION_AVAILABLE = False

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
    print("✅ Enhancement module loaded (8 features)!")
except ImportError as e:
    ENHANCEMENTS_AVAILABLE = False
    print(f"⚠️ Enhancements not available: {e}")"""

    if "ENHANCEMENTS_AVAILABLE" not in content:
        content = content.replace(import_marker, new_import)
        print("✅ Added enhancement import")
    
    # 2. Find where system_content is built and add enhancement context
    # Look for the section where user context is added to system_content
    # We'll add AFTER the existing personalization context
    
    old_pattern = '''        system_content += """
Provide nuanced language help with natural conversation, idioms, and practical vocabulary.
"""'''
    
    new_pattern = '''        system_content += """
Provide nuanced language help with natural conversation, idioms, and practical vocabulary.
"""
        
        # === ENHANCEMENT CONTEXT (8 Features) ===
        if ENHANCEMENTS_AVAILABLE and UNIFIED_MEMORY_AVAILABLE:
            try:
                # Get user settings
                user_country = session["context"]["user"]["preferences"].get("country", "panama")
                user_type_setting = session["context"]["user"]["preferences"].get("user_type", "expat")
                learning_dir = session["context"]["user"]["preferences"].get("learning_direction", "spanish")
                
                # Build enhanced context
                enhancement_ctx = build_enhanced_context(
                    memory_instance=memory,
                    user_type=user_type_setting,
                    country=user_country,
                    learning_direction=learning_dir,
                    current_message=new_message
                )
                
                if enhancement_ctx:
                    system_content += f"\\n{enhancement_ctx}\\n"
                    print(f"✅ Enhanced context added ({len(enhancement_ctx)} chars)")
                    
            except Exception as e:
                print(f"⚠️ Enhancement error (non-fatal): {e}")'''

    if "ENHANCEMENT CONTEXT (8 Features)" not in content:
        content = content.replace(old_pattern, new_pattern)
        print("✅ Added enhancement context injection")
    else:
        print("⏭️ Enhancement context already exists")
    
    # Write back
    with open('/home/ubuntu/EspaLuzFamilybot/main.py', 'w') as f:
        f.write(content)
    
    print("\n✅ Integration complete!")
    print("Run: sudo systemctl restart espaluz-familybot")

if __name__ == "__main__":
    integrate()
