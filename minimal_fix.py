#!/usr/bin/env python3
"""
MINIMAL FIX: Load onboarding data in create_initial_session
This is SAFE - only ADDS functionality, doesn't change existing code
"""

def patch():
    with open('/home/ubuntu/EspaLuzFamilybot/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('/home/ubuntu/EspaLuzFamilybot/main.py.backup-minimal-fix', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Backup created")
    
    # Find the start of create_initial_session and add onboarding loading
    old_start = '''def create_initial_session(user_id, user_info, chat_info, message_text=""):
    """Create a rich context for Claude's MCP with emotional intelligence features"""
    # Detect family member
    family_member = detect_family_member(user_info, message_text) 
    member_info = FAMILY_MEMBERS.get(family_member, FAMILY_MEMBERS["elena"])'''

    new_start = '''def create_initial_session(user_id, user_info, chat_info, message_text=""):
    """Create a rich context for Claude's MCP with emotional intelligence features"""
    
    # ========================================================
    # LOAD SAVED ONBOARDING DATA (Fix for returning users)
    # ========================================================
    saved_onboarding = get_user_onboarding(user_id)
    saved_name = saved_onboarding.get("name") if saved_onboarding.get("step") == "complete" else None
    saved_country = saved_onboarding.get("country") if saved_onboarding.get("step") == "complete" else None
    saved_role = saved_onboarding.get("role") if saved_onboarding.get("step") == "complete" else None
    saved_family = {}
    if saved_onboarding.get("spouse"):
        saved_family["spouse"] = saved_onboarding["spouse"]
    if saved_onboarding.get("children"):
        saved_family["children"] = saved_onboarding["children"]
    # Also sync to unified database if available
    if UNIFIED_MEMORY_AVAILABLE and saved_name:
        try:
            memory = EspaLuzMemory(platform='telegram', platform_user_id=user_id)
            if not memory._user.display_name:
                memory.update_user(display_name=saved_name, current_country=saved_country)
                print(f"🔄 Synced to unified DB: {saved_name}, {saved_country}")
        except Exception as e:
            print(f"⚠️ DB sync error (non-fatal): {e}")
    
    # Detect family member
    family_member = saved_role or detect_family_member(user_info, message_text) 
    member_info = FAMILY_MEMBERS.get(family_member, FAMILY_MEMBERS["elena"])'''

    if "LOAD SAVED ONBOARDING DATA" not in content:
        content = content.replace(old_start, new_start)
        print("✅ Added onboarding loading")
    else:
        print("⏭️ Already patched")
    
    # Now update the preferences section to USE the saved data
    # Find where preferences are set and add the saved values
    old_prefs = '''                "preferences": {
                    "family_role": family_member,
                    "age": member_info["age"],
                    "learning_level": member_info["learning_level"],
                    "interests": member_info["interests"],
                    "tone_preference": member_info["tone"],
                    "primary_language": "russian",
                    "target_languages": ["spanish", "english"],
                    "difficult_words": [],
                    "mastered_words": []
                }'''
    
    new_prefs = '''                "preferences": {
                    "family_role": family_member,
                    "age": member_info["age"],
                    "learning_level": member_info["learning_level"],
                    "interests": member_info["interests"],
                    "tone_preference": member_info["tone"],
                    "primary_language": "russian",
                    "target_languages": ["spanish", "english"],
                    "difficult_words": [],
                    "mastered_words": [],
                    # LOADED FROM SAVED ONBOARDING
                    "user_name": saved_name,
                    "country": saved_country or "panama",
                    "family_members": saved_family
                }'''
    
    if '"user_name": saved_name' not in content:
        content = content.replace(old_prefs, new_prefs)
        print("✅ Added saved preferences")
    else:
        print("⏭️ Preferences already patched")
    
    with open('/home/ubuntu/EspaLuzFamilybot/main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ Minimal fix applied!")
    print("Run: sudo systemctl restart espaluz-familybot")

if __name__ == "__main__":
    patch()
