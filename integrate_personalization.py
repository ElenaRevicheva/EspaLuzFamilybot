#!/usr/bin/env python3
"""
Integration script to add personalization to Telegram bot
Run this on Oracle to patch main.py
"""

import re

def patch_main_py():
    # Read current file
    with open('/home/ubuntu/EspaLuzFamilybot/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('/home/ubuntu/EspaLuzFamilybot/main.py.backup-before-personalization', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Backup created")
    
    # 1. Add import for personalization module (after espaluz_memory import)
    import_pattern = r"(from espaluz_memory import EspaLuzMemory, LANGCHAIN_AVAILABLE\n\s+UNIFIED_MEMORY_AVAILABLE = True)"
    import_replacement = r"""\1

# === PERSONALIZATION ENGINE (NEW - Jan 2026) ===
try:
    from espaluz_personalization import EspaLuzPersonalization, extract_name_from_message, extract_country_from_message, COUNTRY_GREETINGS
    PERSONALIZATION_AVAILABLE = True
    print("✅ Personalization engine loaded!")
except ImportError as e:
    PERSONALIZATION_AVAILABLE = False
    print(f"⚠️ Personalization not available: {e}")"""
    
    if "PERSONALIZATION_AVAILABLE" not in content:
        content = re.sub(import_pattern, import_replacement, content)
        print("✅ Added personalization import")
    else:
        print("⏭️ Personalization import already exists")
    
    # 2. Find the area where system_content is built and inject personalization context
    # Look for: user_name = session["context"]["user"]["preferences"].get("user_name",
    old_user_context = '''    else:  # default adult user
        # Get user name from onboarding or session
        user_name = session["context"]["user"]["preferences"].get("user_name", 
                    session["context"]["user"].get("first_name", "friend"))
        user_country = session["context"]["user"]["preferences"].get("country", "Panama").replace("_", " ").title()
        user_role = session["context"]["user"]["preferences"].get("family_role", "learner")
        family_info = session["context"]["user"]["preferences"].get("family_members", {})
        
        system_content += f"""
You're speaking with {user_name}, who is learning Spanish and English in {user_country}.
Role: {user_role}. At an intermediate level.
"""
        # Add family context if available
        if family_info:
            system_content += f"Family: {family_info}\\n"
        
        system_content += """
Provide nuanced language assistance focused on natural conversation, idioms, and practical vocabulary. 
Use vocabulary appropriate for their level. ALWAYS address them by their actual name, not "Elena".
"""'''

    new_user_context = '''    else:  # default adult user
        # =====================================================
        # 🎯 ENHANCED PERSONALIZATION FROM DATABASE (Jan 2026)
        # =====================================================
        # Try to get rich context from unified database first
        personalized_context = ""
        db_user_name = None
        db_country = None
        db_emotional_trend = None
        
        if UNIFIED_MEMORY_AVAILABLE and PERSONALIZATION_AVAILABLE:
            try:
                # Initialize memory for this user
                memory = EspaLuzMemory(platform='telegram', platform_user_id=user_id)
                personalizer = EspaLuzPersonalization(memory)
                
                # Get detected country from session or DB
                session_country = session["context"]["user"]["preferences"].get("country")
                
                # Build full personalized context
                full_context = personalizer.build_full_context(
                    detected_country=session_country,
                    current_emotion=emotion
                )
                
                # Extract key values
                db_user_name = full_context.user_name or None
                db_country = full_context.country if full_context.country != "unknown" else None
                db_emotional_trend = full_context.emotional_trend
                
                # Use the pre-built context string
                personalized_context = full_context.context_string
                
                print(f"✅ Personalization loaded: name={db_user_name}, country={db_country}, trend={db_emotional_trend}")
                
            except Exception as e:
                print(f"⚠️ Personalization error (using fallback): {e}")
        
        # Fallback to session data if DB doesn't have info
        user_name = db_user_name or session["context"]["user"]["preferences"].get("user_name", 
                    session["context"]["user"].get("first_name", None))
        user_country = db_country or session["context"]["user"]["preferences"].get("country", "Panama")
        user_country = user_country.replace("_", " ").title()
        user_role = session["context"]["user"]["preferences"].get("family_role", "learner")
        family_info = session["context"]["user"]["preferences"].get("family_members", {})
        
        # If we have personalized context from DB, use it
        if personalized_context:
            system_content += f"""
{personalized_context}
"""
        else:
            # Fallback to basic context
            name_display = user_name if user_name else "this learner (ask for their name!)"
            system_content += f"""
You're speaking with {name_display}, who is learning Spanish and English in {user_country}.
Role: {user_role}. At an intermediate level.
"""
            if family_info:
                system_content += f"Family: {family_info}\\n"
        
        # Add critical instruction about names
        if not user_name:
            system_content += """
⚠️ IMPORTANT: You don't know this user's name yet!
- DO NOT say "Hola, friend" or "Hello, amigo" - this sounds generic and impersonal
- Instead, naturally ask: "By the way, what's your name?" or "¿Cómo te llamas?"
- Once they tell you, use their actual name in responses
"""
        else:
            system_content += f"""
⚠️ CRITICAL: Always address this user as "{user_name}" - NEVER say "friend" or generic greetings!
"""
        
        system_content += """
Provide nuanced language assistance focused on natural conversation, idioms, and practical vocabulary. 
Use vocabulary appropriate for their level.
"""'''

    if "ENHANCED PERSONALIZATION FROM DATABASE" not in content:
        content = content.replace(old_user_context, new_user_context)
        print("✅ Added personalization context injection")
    else:
        print("⏭️ Personalization context already exists")
    
    # 3. Add name/country extraction from messages
    # Find the unified memory tracking section and add name extraction
    old_memory_tracking = '''    # === UNIFIED MEMORY TRACKING (NEW - Jan 2026) ===
    # Store conversation in unified database for cross-platform memory
    if UNIFIED_MEMORY_AVAILABLE:
        try:
            memory = EspaLuzMemory(platform='telegram', platform_user_id=user_id)
            memory.track_message()'''
    
    new_memory_tracking = '''    # === UNIFIED MEMORY TRACKING (NEW - Jan 2026) ===
    # Store conversation in unified database for cross-platform memory
    if UNIFIED_MEMORY_AVAILABLE:
        try:
            memory = EspaLuzMemory(platform='telegram', platform_user_id=user_id)
            memory.track_message()
            
            # === AUTO-EXTRACT NAME AND COUNTRY FROM USER MESSAGES ===
            if PERSONALIZATION_AVAILABLE:
                # Try to extract name if we don't have one
                if not memory._user.display_name:
                    extracted_name = extract_name_from_message(user_input)
                    if extracted_name:
                        memory.update_user(display_name=extracted_name)
                        print(f"✨ Extracted and saved user name: {extracted_name}")
                
                # Try to extract country if we don't have one
                if not memory._user.current_country:
                    extracted_country = extract_country_from_message(user_input)
                    if extracted_country:
                        memory.update_user(current_country=extracted_country)
                        print(f"🌎 Extracted and saved user country: {extracted_country}")'''
    
    if "AUTO-EXTRACT NAME AND COUNTRY" not in content:
        content = content.replace(old_memory_tracking, new_memory_tracking)
        print("✅ Added name/country auto-extraction")
    else:
        print("⏭️ Name/country extraction already exists")
    
    # Write updated file
    with open('/home/ubuntu/EspaLuzFamilybot/main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ Telegram bot patched successfully!")
    print("Restart with: sudo systemctl restart espaluz-familybot")

if __name__ == "__main__":
    patch_main_py()
