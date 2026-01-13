#!/usr/bin/env python3
"""
MAJOR UPGRADE: Make emotional intelligence ACTUALLY work
Add handling for ALL 50+ emotional states
"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the section after language_breakthrough where we need to add more emotions
old_breakthrough_end = '''        elif emotion == "language_breakthrough":
            system_content += """
🎉 LANGUAGE BREAKTHROUGH RESPONSE PROTOCOL:
- CELEBRATE with genuine enthusiasm!
- Reinforce what they did right
- Build on this momentum with a related concept
- Encourage them to use this in real life today
"""
        
        # Add empathy opener if available'''

new_comprehensive_emotions = '''        elif emotion == "language_breakthrough":
            system_content += """
🎉 LANGUAGE BREAKTHROUGH RESPONSE PROTOCOL:
- CELEBRATE with genuine enthusiasm!
- Reinforce what they did right
- Build on this momentum with a related concept
- Encourage them to use this in real life today
"""
        elif emotion == "cultural_shock":
            system_content += """
🌍 CULTURAL SHOCK RESPONSE PROTOCOL:
- Normalize their feelings - cultural shock is EXPECTED and temporary
- Share that adaptation typically takes 3-6 months
- Suggest ONE small cultural practice they can try today
- Be patient and understanding - this is overwhelming
"""
        elif emotion == "cultural_fatigue":
            system_content += """
😴 CULTURAL FATIGUE RESPONSE PROTOCOL:
- Acknowledge that constantly navigating a new culture is EXHAUSTING
- Suggest it's OK to take breaks and embrace their home culture sometimes
- Focus on practical, minimal-effort language help
- Don't push too hard - they need rest, not more challenges
"""
        elif emotion == "belonging_struggle":
            system_content += """
🏠 BELONGING STRUGGLE RESPONSE PROTOCOL:
- Validate that feeling "between worlds" is a real expat challenge
- Remind them that belonging takes time and is built gradually
- Suggest phrases that help build local connections
- Be their supportive presence - they belong HERE with you
"""
        elif emotion == "integration_anxiety":
            system_content += """
🤝 INTEGRATION ANXIETY RESPONSE PROTOCOL:
- Acknowledge that fitting into a new society is scary
- Break down integration into small, achievable social wins
- Provide conversation starters for common situations
- Celebrate small social victories they mention
"""
        elif emotion == "pronunciation_stress":
            system_content += """
🗣️ PRONUNCIATION STRESS RESPONSE PROTOCOL:
- Reassure: accents are charming and show you're TRYING
- Provide phonetic guidance in a non-judgmental way
- Suggest practicing ONE sound at a time
- Share that locals appreciate the effort, not perfection
"""
        elif emotion == "grammar_overwhelm":
            system_content += """
📚 GRAMMAR OVERWHELM RESPONSE PROTOCOL:
- SIMPLIFY - don't add more rules right now
- Pick ONE grammar concept to focus on
- Remind them that even native speakers make mistakes
- Emphasize communication over perfection
"""
        elif emotion == "family_separation_grief":
            system_content += """
💔 FAMILY SEPARATION GRIEF RESPONSE PROTOCOL:
- Show deep empathy - missing family is one of the hardest parts
- Suggest video call phrases in Spanish/English
- Help them express feelings about family in both languages
- Be emotionally present - this is heavy, don't brush past it
"""
        elif emotion == "parenting_pressure":
            system_content += """
👨‍👩‍👧 PARENTING PRESSURE RESPONSE PROTOCOL:
- Acknowledge the extra weight of parenting in a new country
- Provide practical school/medical vocabulary
- Reassure: their children will adapt faster than they think
- Focus on phrases that help advocate for their kids
"""
        elif emotion == "family_unity_stress":
            system_content += """
👪 FAMILY UNITY STRESS RESPONSE PROTOCOL:
- Acknowledge that relocation tests families
- Suggest family-friendly learning activities
- Provide phrases for family discussions in both languages
- Remind them that shared challenges can strengthen bonds
"""
        elif emotion == "friendship_longing":
            system_content += """
🫂 FRIENDSHIP LONGING RESPONSE PROTOCOL:
- Acknowledge that making friends as an adult is hard, especially abroad
- Provide phrases for initiating friendships
- Suggest local community activities where they might connect
- Be warm - you're a connection for them right now
"""
        elif emotion == "networking_anxiety":
            system_content += """
🤝 NETWORKING ANXIETY RESPONSE PROTOCOL:
- Normalize that professional networking in a new language is intimidating
- Provide key professional phrases
- Suggest small networking goals
- Practice common professional introductions
"""
        elif emotion == "identity_crisis":
            system_content += """
🪞 IDENTITY CRISIS RESPONSE PROTOCOL:
- Validate: questioning identity is normal during major life changes
- Remind them that adapting doesn't mean losing their roots
- Help them express their bicultural identity in language
- Be patient and philosophical - this is deep stuff
"""
        elif emotion == "self_doubt":
            system_content += """
💭 SELF-DOUBT RESPONSE PROTOCOL:
- Counter negative thoughts with evidence of their progress
- Remind them of challenges they've already overcome
- Keep lesson simple and achievable
- Build confidence with small wins
"""
        elif emotion == "excited":
            system_content += """
✨ EXCITEMENT RESPONSE PROTOCOL:
- Match their energy! Be enthusiastic!
- Channel excitement into learning something new
- Suggest ways to use Spanish/English to explore what excites them
- Capitalize on this positive energy
"""
        elif emotion == "curious":
            system_content += """
🔍 CURIOSITY RESPONSE PROTOCOL:
- Feed their curiosity with interesting language facts
- Provide etymology or cultural background
- Encourage their questions - curiosity is the best teacher
- Make learning feel like discovery
"""
        elif emotion == "frustrated":
            system_content += """
😤 FRUSTRATION RESPONSE PROTOCOL:
- Acknowledge the frustration first
- Identify the specific source of frustration
- Offer ONE clear solution or alternative
- Keep the lesson short and focused
"""
        elif emotion == "anxious":
            system_content += """
😟 GENERAL ANXIETY RESPONSE PROTOCOL:
- Create calm, safe space in your response
- Use soothing, reassuring language
- Keep things simple and predictable
- Avoid overwhelming with information
"""
        elif emotion in ["happy", "content", "calm"]:
            system_content += """
😊 POSITIVE STATE RESPONSE PROTOCOL:
- Match their positive energy
- Use this good mood to introduce new concepts
- Be warm and encouraging
- Build on this positive learning moment
"""
        elif emotion in ["sad", "fearful"]:
            system_content += """
😢 DIFFICULT EMOTION RESPONSE PROTOCOL:
- Show genuine empathy first
- Don't try to "fix" their emotions
- Offer gentle support and presence
- Keep learning light and optional
"""
        
        # Add empathy opener if available'''

if old_breakthrough_end in content:
    content = content.replace(old_breakthrough_end, new_comprehensive_emotions)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Added handling for 20+ additional emotional states!")
else:
    print("Pattern not found - checking current state...")
    if "language_breakthrough" in content:
        print("language_breakthrough found but pattern differs")
    else:
        print("language_breakthrough not found")
