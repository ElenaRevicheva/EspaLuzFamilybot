#!/usr/bin/env python3
"""
EspaLuz Demo Mode for Workshop Presentations
Enables presentation-friendly responses showing emotional intelligence features
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Demo mode storage
DEMO_SESSIONS_FILE = "demo_sessions.json"


class DemoMode:
    """Manages demo/presentation mode for workshop demonstrations"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(__file__)
        self.sessions_file = os.path.join(self.base_dir, DEMO_SESSIONS_FILE)
        self._ensure_file()
    
    def _ensure_file(self):
        """Ensure sessions file exists"""
        if not os.path.exists(self.sessions_file):
            with open(self.sessions_file, 'w') as f:
                json.dump({}, f, indent=2)
    
    def _load_sessions(self) -> Dict:
        """Load demo sessions"""
        try:
            with open(self.sessions_file, 'r') as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_sessions(self, sessions: Dict):
        """Save demo sessions"""
        with open(self.sessions_file, 'w') as f:
            json.dump(sessions, f, indent=2)
    
    def is_demo_active(self, user_id: str) -> bool:
        """Check if demo mode is active for user"""
        sessions = self._load_sessions()
        user_id_str = str(user_id)
        
        if user_id_str not in sessions:
            return False
        
        return sessions[user_id_str].get("active", False)
    
    def activate_demo(self, user_id: str) -> str:
        """Activate demo mode for a user"""
        sessions = self._load_sessions()
        user_id_str = str(user_id)
        
        sessions[user_id_str] = {
            "active": True,
            "activated_at": datetime.now().isoformat(),
            "interactions": 0
        }
        
        self._save_sessions(sessions)
        
        return """🎬 **DEMO MODE ACTIVATED**
━━━━━━━━━━━━━━━━━━━━

Welcome to EspaLuz Workshop Presentation Mode!

In this mode, I will:
• Show my emotional intelligence in action
• Display how I detect user emotions
• Demonstrate family-aware personalization
• Highlight country-specific knowledge

✨ **Try these demo scenarios:**

1️⃣ Say: "I'm feeling frustrated with Spanish"
   → Watch me detect LANGUAGE_ANXIETY

2️⃣ Say: "I miss my family back home"
   → Watch me detect HOMESICKNESS

3️⃣ Say: "I need to open a bank account"
   → Watch country-specific guidance

4️⃣ Say: "My daughter doesn't want to speak Spanish"
   → Watch family-aware response

━━━━━━━━━━━━━━━━━━━━
📌 Type /demo off to exit demo mode
"""
    
    def deactivate_demo(self, user_id: str) -> str:
        """Deactivate demo mode"""
        sessions = self._load_sessions()
        user_id_str = str(user_id)
        
        if user_id_str in sessions:
            sessions[user_id_str]["active"] = False
            sessions[user_id_str]["deactivated_at"] = datetime.now().isoformat()
            self._save_sessions(sessions)
        
        return """🎬 **DEMO MODE DEACTIVATED**

Back to normal conversation mode.
Thanks for exploring EspaLuz!

/help - See all commands
/menu - Full feature list
"""
    
    def increment_interaction(self, user_id: str):
        """Track demo interactions"""
        sessions = self._load_sessions()
        user_id_str = str(user_id)
        
        if user_id_str in sessions:
            sessions[user_id_str]["interactions"] = sessions[user_id_str].get("interactions", 0) + 1
            self._save_sessions(sessions)
    
    def get_demo_response_wrapper(self, original_response: str, emotion_detected: str, 
                                   calibration: Dict, country: str = None) -> str:
        """Wrap response with demo insights showing how EI works"""
        
        demo_header = """
╔══════════════════════════════════════════════╗
║  🧠 EMOTIONAL INTELLIGENCE - BEHIND SCENES   ║
╠══════════════════════════════════════════════╣
"""
        
        # Emotion detection showcase
        emotion_section = f"""║ 🎯 EMOTION DETECTED: {emotion_detected.upper()}
║ 
║ Intensity: {calibration.get('intensity', 'moderate').title()}
║ Category: {calibration.get('category', 'general').title()}
"""
        
        # Response calibration showcase
        calibration_section = f"""║ 
║ 📊 RESPONSE CALIBRATION:
║ • Tone: {calibration.get('tone', 'warm').title()}
║ • Pacing: {calibration.get('pacing', 'natural').title()}
║ • Empathy Level: {calibration.get('empathy_level', 'high').title()}
"""
        
        # Country context if available
        country_section = ""
        if country:
            country_section = f"""║ 
║ 🌎 COUNTRY CONTEXT: {country.upper()}
║ • Using local vocabulary and phrases
║ • Banking, healthcare, schools adapted
"""
        
        demo_footer = """╚══════════════════════════════════════════════╝

"""
        
        # Assemble demo response
        full_demo = demo_header + emotion_section + calibration_section + country_section + demo_footer
        
        # Add the actual response with visual separator
        actual_response = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 MY RESPONSE (calibrated for your emotion):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{original_response}
"""
        
        return full_demo + actual_response
    
    def get_demo_scenarios(self) -> str:
        """Get list of demo scenarios for presenters"""
        return """🎭 **DEMO SCENARIOS FOR PRESENTERS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Emotional Intelligence Demos:**

1️⃣ **Language Anxiety**
   Say: "I'm so frustrated, everyone speaks too fast"
   Shows: Empathetic response, encouragement

2️⃣ **Homesickness**
   Say: "I really miss my mom's cooking"
   Shows: Emotional validation, cultural bridge

3️⃣ **Cultural Shock**
   Say: "Why does everything work differently here?"
   Shows: Normalization, practical guidance

4️⃣ **Urgency Stress**
   Say: "I have a meeting in 30 minutes and need help!"
   Shows: Quick, focused response

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Country-Specific Demos:**

5️⃣ **Banking (Panama)**
   Say: "How do I open a bank account?"
   Shows: Banco General, Banistmo specifics

6️⃣ **Healthcare (Mexico)**
   Say: "I need to see a doctor"
   Shows: IMSS, private clinic options

7️⃣ **Local Slang (Colombia)**
   Say: "Teach me some local expressions"
   Shows: Parcero, bacano, etc.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Family-Aware Demos:**

8️⃣ **Parent Concern**
   Say: "My child refuses to speak Spanish at home"
   Shows: Family dynamics understanding

9️⃣ **Partner Learning**
   Say: "I want to help my spouse learn too"
   Shows: Couple learning strategies

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Voice & Media Demos:**

🔟 Send a voice message in Spanish
   Shows: Voice processing + feedback

1️⃣1️⃣ Send a photo of text
   Shows: OCR translation capability

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


# Demo emotion showcase data
DEMO_EMOTIONS = {
    "frustrated": {
        "detected": "LANGUAGE_ANXIETY",
        "category": "Learning Emotions",
        "intensity": "moderate-high",
        "calibration": {
            "tone": "warm and encouraging",
            "pacing": "slower, reassuring",
            "empathy_level": "high",
            "approach": "validation + practical tips"
        }
    },
    "miss": {
        "detected": "HOMESICKNESS",
        "category": "Expat-Specific",
        "intensity": "high",
        "calibration": {
            "tone": "deeply empathetic",
            "pacing": "gentle, unhurried",
            "empathy_level": "maximum",
            "approach": "emotional validation first"
        }
    },
    "confused": {
        "detected": "CULTURAL_SHOCK",
        "category": "Expat-Specific",
        "intensity": "moderate",
        "calibration": {
            "tone": "normalizing",
            "pacing": "patient",
            "empathy_level": "high",
            "approach": "normalize + explain"
        }
    },
    "urgent": {
        "detected": "URGENCY_STRESS",
        "category": "Real-Life Emotions",
        "intensity": "high",
        "calibration": {
            "tone": "focused, direct",
            "pacing": "quick, efficient",
            "empathy_level": "moderate",
            "approach": "solution-first"
        }
    },
    "excited": {
        "detected": "BREAKTHROUGH_JOY",
        "category": "Learning Emotions",
        "intensity": "high",
        "calibration": {
            "tone": "celebratory",
            "pacing": "energetic",
            "empathy_level": "enthusiastic",
            "approach": "celebrate + build on success"
        }
    },
    "scared": {
        "detected": "FEAR_OF_FAILURE",
        "category": "Learning Emotions",
        "intensity": "moderate-high",
        "calibration": {
            "tone": "reassuring",
            "pacing": "calm, steady",
            "empathy_level": "high",
            "approach": "normalize + encourage"
        }
    }
}


def detect_demo_emotion(message: str) -> Dict[str, Any]:
    """Detect emotion for demo purposes with rich metadata"""
    message_lower = message.lower()
    
    for keyword, data in DEMO_EMOTIONS.items():
        if keyword in message_lower:
            return data
    
    # Default neutral state
    return {
        "detected": "NEUTRAL_ENGAGED",
        "category": "General",
        "intensity": "normal",
        "calibration": {
            "tone": "friendly",
            "pacing": "natural",
            "empathy_level": "balanced",
            "approach": "conversational"
        }
    }


# Global instance
demo_mode = DemoMode()
