#!/usr/bin/env python3
"""
UPGRADE: Make family context ACTUALLY affect responses
Add deep personalization based on family members
"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find where family info is added to prompt and enhance it
old_family_section = '''    if family_members:
        if family_members.get("spouse"):
            personalization += f"- Spouse: {family_members['spouse']}\\n"
        if family_members.get("children"):
            kids = [f"{c['name']} ({c['age']}yo)" for c in family_members["children"]]
            personalization += f"- Children: {', '.join(kids)}\\n"'''

new_family_section = '''    if family_members:
        personalization += "\\n👨‍👩‍👧 FAMILY-AWARE PERSONALIZATION ACTIVE:\\n"
        
        if family_members.get("spouse"):
            spouse_name = family_members['spouse']
            personalization += f"""
💑 SPOUSE: {spouse_name}
- Occasionally mention phrases they can practice TOGETHER with {spouse_name}
- Consider couple-specific scenarios (restaurants, travel, home)
- If appropriate, suggest how {spouse_name} could help with learning
"""
        
        if family_members.get("children"):
            children = family_members["children"]
            personalization += "\\n👶 CHILDREN:\\n"
            for child in children:
                name = child.get('name', 'child')
                age = child.get('age', 0)
                
                if age <= 5:
                    personalization += f"""
🧒 {name} (age {age} - TODDLER/PRESCHOOL):
- Suggest simple Spanish words they can teach {name} together
- Mention playful learning activities suitable for {name}'s age
- Reference things a {age}-year-old would like (animals, colors, cartoons)
- Phrases for daycare/preschool situations
"""
                elif age <= 10:
                    personalization += f"""
🧒 {name} (age {age} - ELEMENTARY):
- Suggest homework-help phrases
- School vocabulary for {name}'s grade level
- Phrases for parent-teacher conferences
- Sports/activities vocabulary {name} might need
"""
                elif age <= 15:
                    personalization += f"""
👦 {name} (age {age} - TWEEN/TEEN):
- Acknowledge that teenagers often learn language faster
- Suggest phrases for {name}'s social situations
- Help with school project vocabulary
- Possibly {name} can help the parent practice!
"""
                else:
                    personalization += f"""
🧑 {name} (age {age} - OLDER TEEN/ADULT):
- {name} might be more independent with language
- Focus on phrases for adult family coordination
- Career/university vocabulary if relevant
"""
            
            # Add general family learning advice
            personalization += """
🏠 FAMILY LEARNING TIPS TO WEAVE IN:
- Suggest family Spanish dinner table games
- Recommend labeling items at home in Spanish
- Encourage watching Spanish shows together
- Make learning a FAMILY activity, not just individual
"""'''

if old_family_section in content:
    content = content.replace(old_family_section, new_family_section)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Enhanced family-aware personalization!")
else:
    print("Pattern not found - checking...")
    if "family_members.get(\"spouse\")" in content:
        print("Family section exists but pattern differs")
    else:
        print("Family section not found")
