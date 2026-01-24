#!/usr/bin/env python3
"""Fix the None name case - tell Claude to ask for name if missing"""

with open('/home/ubuntu/EspaLuzFamilybot/main.py', 'r') as f:
    content = f.read()

# Find and replace the prompt building section
old_section = '''    else:  # default adult user
        # Get user name from onboarding or session
        user_name = session["context"]["user"]["preferences"].get("user_name", 
                    session["context"]["user"].get("first_name"))
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

new_section = '''    else:  # default adult user
        # Get user name from onboarding or session
        user_name = session["context"]["user"]["preferences"].get("user_name") or session["context"]["user"].get("first_name")
        user_country = session["context"]["user"]["preferences"].get("country", "Panama").replace("_", " ").title()
        user_role = session["context"]["user"]["preferences"].get("family_role", "learner")
        family_info = session["context"]["user"]["preferences"].get("family_members", {})
        
        if user_name:
            system_content += f"""
👤 USER: {user_name} from {user_country}
Role: {user_role}. Level: intermediate.
⚠️ ALWAYS address them as "{user_name}" - NEVER say "friend" or "amigo"!
"""
        else:
            system_content += f"""
👤 USER: Name unknown (from {user_country})
⚠️ IMPORTANT: You don't know this user's name yet!
- DO NOT say "Hola, friend" or "amigo" - this is impersonal!
- Naturally ask: "By the way, ¿cómo te llamas?" or "What's your name?"
- Once they tell you, use their actual name in all responses!
"""
        
        # Add family context if available
        if family_info:
            system_content += f"Family: {family_info}\\n"
        
        system_content += """
Provide nuanced language assistance focused on natural conversation, idioms, and practical vocabulary.
"""'''

if "Name unknown" not in content:
    content = content.replace(old_section, new_section)
    print("✅ Fixed None name handling!")
else:
    print("⏭️ Already fixed")

with open('/home/ubuntu/EspaLuzFamilybot/main.py', 'w') as f:
    f.write(content)

print("Done!")
