"""
EspaLuz Personalization Engine
==============================
Makes responses TRULY personalized with:
- User's actual name (not "friend" or "hola amigo")
- Country-specific context (21 Spanish-speaking countries)
- Family member awareness
- Emotional history from database
- Learning journey tracking

Created: January 22, 2026
Author: CTO AIPA
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ============================================================================
# COUNTRY-SPECIFIC PERSONALIZATION (21 Spanish-Speaking Countries)
# ============================================================================

COUNTRY_GREETINGS = {
    # CENTRAL AMERICA
    "panama": {
        "greeting": "¡Qué xopa",
        "formal_greeting": "¡Buenos días",
        "casual_name": "parcero/a",
        "currency": "Balboa (USD)",
        "timezone": "EST (UTC-5)",
        "local_flavor": "Panama is the hub of the Americas! Great ceviche, Canal vibes, and 'juega vivo' culture.",
        "slang": ["xopa", "fren", "pela'o", "chombo", "yeye"],
        "topics": ["Canal", "Casco Viejo", "Bocas del Toro", "sancocho", "ceviche"]
    },
    "costa_rica": {
        "greeting": "¡Pura vida",
        "formal_greeting": "¡Buenos días",
        "casual_name": "mae",
        "currency": "Colón (CRC)",
        "timezone": "CST (UTC-6)",
        "local_flavor": "Costa Rica - no army, lots of nature! Ticos are super friendly.",
        "slang": ["pura vida", "mae", "tuanis", "tico/a", "chunche"],
        "topics": ["playas", "volcanes", "biodiversidad", "gallo pinto", "café"]
    },
    "guatemala": {
        "greeting": "¡Qué onda",
        "formal_greeting": "¡Buenos días",
        "casual_name": "vos",
        "currency": "Quetzal (GTQ)",
        "timezone": "CST (UTC-6)",
        "local_flavor": "Guatemala - land of eternal spring and Mayan heritage.",
        "slang": ["qué onda", "canche", "patojo", "chilero", "shuco"],
        "topics": ["Antigua", "Tikal", "volcanes", "textiles", "tamales"]
    },
    "honduras": {
        "greeting": "¡Qué ondas",
        "formal_greeting": "¡Buenos días",
        "casual_name": "maje",
        "currency": "Lempira (HNL)",
        "timezone": "CST (UTC-6)",
        "local_flavor": "Honduras - Copán ruins and Caribbean coast vibes.",
        "slang": ["maje", "catracho", "cipote", "alero", "cheque"],
        "topics": ["Copán", "Roatán", "baleadas", "café", "mariscos"]
    },
    "el_salvador": {
        "greeting": "¡Qué onda",
        "formal_greeting": "¡Buenos días",
        "casual_name": "vos",
        "currency": "USD",
        "timezone": "CST (UTC-6)",
        "local_flavor": "El Salvador - pupusas, Bitcoin, and surfing!",
        "slang": ["chivo", "bicho", "cipote", "chucho", "guanaco"],
        "topics": ["pupusas", "playas", "volcanes", "Bitcoin", "artesanías"]
    },
    "nicaragua": {
        "greeting": "¡Qué onda",
        "formal_greeting": "¡Buenos días",
        "casual_name": "maje",
        "currency": "Córdoba (NIO)",
        "timezone": "CST (UTC-6)",
        "local_flavor": "Nicaragua - land of lakes and volcanoes, poetic spirit.",
        "slang": ["tuani", "nica", "maje", "chunche", "pinolero"],
        "topics": ["Granada", "León", "volcanes", "gallo pinto", "poesía"]
    },
    
    # CARIBBEAN
    "cuba": {
        "greeting": "¡Oye, qué bolá",
        "formal_greeting": "¡Buenos días",
        "casual_name": "asere",
        "currency": "Peso Cubano (CUP)",
        "timezone": "EST (UTC-5)",
        "local_flavor": "Cuba - music, vintage cars, and revolutionary spirit!",
        "slang": ["qué bolá", "asere", "yuma", "guagua", "fula"],
        "topics": ["salsa", "Habana Vieja", "mojitos", "béisbol", "carros clásicos"]
    },
    "dominican_republic": {
        "greeting": "¡Klk",  # Qué lo que
        "formal_greeting": "¡Buenos días",
        "casual_name": "manito/a",
        "currency": "Peso Dominicano (DOP)",
        "timezone": "AST (UTC-4)",
        "local_flavor": "Dominican Republic - merengue, baseball, and Caribbean sun!",
        "slang": ["klk", "tato", "vaina", "tigueraje", "jevi"],
        "topics": ["merengue", "bachata", "playas", "mangú", "béisbol"]
    },
    "puerto_rico": {
        "greeting": "¡Wepa",
        "formal_greeting": "¡Buenos días",
        "casual_name": "bro/nena",
        "currency": "USD",
        "timezone": "AST (UTC-4)",
        "local_flavor": "Puerto Rico - Boricua pride, reggaetón, and mofongo!",
        "slang": ["wepa", "brutal", "chavos", "janguear", "corillo"],
        "topics": ["reggaetón", "Old San Juan", "mofongo", "playas", "Yunque"]
    },
    
    # SOUTH AMERICA
    "mexico": {
        "greeting": "¡Qué onda",
        "formal_greeting": "¡Buenos días",
        "casual_name": "güey/wey",
        "currency": "Peso Mexicano (MXN)",
        "timezone": "Various (UTC-8 to UTC-5)",
        "local_flavor": "Mexico - tacos, mariachi, and incredible diversity!",
        "slang": ["güey", "chido", "neta", "órale", "chamba"],
        "topics": ["tacos", "tequila", "mariachi", "CDMX", "playas"]
    },
    "colombia": {
        "greeting": "¡Quiubo",
        "formal_greeting": "¡Buenos días",
        "casual_name": "parcero/a",
        "currency": "Peso Colombiano (COP)",
        "timezone": "COT (UTC-5)",
        "local_flavor": "Colombia - coffee, cumbia, and incredible warmth!",
        "slang": ["parcero", "bacano", "chévere", "parce", "berraco"],
        "topics": ["café", "Cartagena", "Medellín", "arepas", "cumbia"]
    },
    "venezuela": {
        "greeting": "¡Épale",
        "formal_greeting": "¡Buenos días",
        "casual_name": "pana",
        "currency": "Bolívar (VES)",
        "timezone": "VET (UTC-4)",
        "local_flavor": "Venezuela - arepas, Angel Falls, and warm hearts despite challenges.",
        "slang": ["pana", "chévere", "fino", "marico", "arrecho"],
        "topics": ["arepas", "Salto Ángel", "béisbol", "hallacas", "playas"]
    },
    "ecuador": {
        "greeting": "¡Qué más",
        "formal_greeting": "¡Buenos días",
        "casual_name": "ñaño/a",
        "currency": "USD",
        "timezone": "ECT (UTC-5)",
        "local_flavor": "Ecuador - Galápagos, the equator line, and ceviche!",
        "slang": ["ñaño", "chuchaqui", "bacán", "simon", "nel"],
        "topics": ["Galápagos", "Quito", "ceviche", "sombreros", "volcanes"]
    },
    "peru": {
        "greeting": "¡Habla",
        "formal_greeting": "¡Buenos días",
        "casual_name": "causa",
        "currency": "Sol (PEN)",
        "timezone": "PET (UTC-5)",
        "local_flavor": "Peru - ceviche capital, Machu Picchu, and culinary heaven!",
        "slang": ["causa", "pata", "chévere", "jato", "bravazo"],
        "topics": ["ceviche", "Machu Picchu", "pisco", "Lima", "quinoa"]
    },
    "bolivia": {
        "greeting": "¡Qué tal",
        "formal_greeting": "¡Buenos días",
        "casual_name": "che",
        "currency": "Boliviano (BOB)",
        "timezone": "BOT (UTC-4)",
        "local_flavor": "Bolivia - Salar de Uyuni, indigenous heritage, and altitude!",
        "slang": ["yapa", "chango", "jailón", "k'enko", "polera"],
        "topics": ["Salar", "La Paz", "cholitas", "salteñas", "Carnaval"]
    },
    "chile": {
        "greeting": "¡Hola po",
        "formal_greeting": "¡Buenos días",
        "casual_name": "weón/weona",
        "currency": "Peso Chileno (CLP)",
        "timezone": "CLT (UTC-3/-4)",
        "local_flavor": "Chile - wine, Patagonia, and unique slang (chilenismos)!",
        "slang": ["po", "weón", "cachai", "fome", "bacán"],
        "topics": ["vino", "Patagonia", "Atacama", "empanadas", "pisco"]
    },
    "argentina": {
        "greeting": "¡Che, qué onda",
        "formal_greeting": "¡Buen día",
        "casual_name": "che",
        "currency": "Peso Argentino (ARS)",
        "timezone": "ART (UTC-3)",
        "local_flavor": "Argentina - tango, asado, Messi, and passionate souls!",
        "slang": ["che", "boludo", "bárbaro", "quilombo", "morfar"],
        "topics": ["tango", "asado", "fútbol", "mate", "Buenos Aires"]
    },
    "uruguay": {
        "greeting": "¡Bo, qué hacés",
        "formal_greeting": "¡Buen día",
        "casual_name": "bo",
        "currency": "Peso Uruguayo (UYU)",
        "timezone": "UYT (UTC-3)",
        "local_flavor": "Uruguay - mate, chivitos, and a chill vibe!",
        "slang": ["bo", "ta", "championes", "celeste", "gurí"],
        "topics": ["mate", "asado", "fútbol", "Punta del Este", "candombe"]
    },
    "paraguay": {
        "greeting": "¡Mba'éichapa",  # Guaraní greeting
        "formal_greeting": "¡Buenos días",
        "casual_name": "che",
        "currency": "Guaraní (PYG)",
        "timezone": "PYT (UTC-4)",
        "local_flavor": "Paraguay - bilingual (Spanish/Guaraní), tereré, and chipa!",
        "slang": ["che", "mita'i", "kuña", "karai", "py"],
        "topics": ["tereré", "chipa", "Guaraní", "harp", "Itaipú"]
    },
    
    # EUROPE
    "spain": {
        "greeting": "¡Hola, qué tal",
        "formal_greeting": "¡Buenos días",
        "casual_name": "tío/tía",
        "currency": "Euro (EUR)",
        "timezone": "CET (UTC+1/+2)",
        "local_flavor": "Spain - tapas, siestas, and regional diversity!",
        "slang": ["tío", "mola", "guay", "currar", "flipar"],
        "topics": ["tapas", "paella", "fútbol", "flamenco", "Madrid/Barcelona"]
    },
    
    # AFRICA
    "equatorial_guinea": {
        "greeting": "¡Hola",
        "formal_greeting": "¡Buenos días",
        "casual_name": "hermano/a",
        "currency": "Franco CFA (XAF)",
        "timezone": "WAT (UTC+1)",
        "local_flavor": "Equatorial Guinea - Africa's only Spanish-speaking country!",
        "slang": ["eah", "cha", "compa"],
        "topics": ["petróleo", "selva", "Malabo", "Bioko", "cultura Fang"]
    }
}

# Default for unknown country
DEFAULT_COUNTRY = {
    "greeting": "¡Hola",
    "formal_greeting": "¡Buenos días",
    "casual_name": "",
    "currency": "varies",
    "timezone": "varies",
    "local_flavor": "Spanish is spoken across 21 countries with beautiful diversity!",
    "slang": [],
    "topics": []
}


@dataclass
class PersonalizedContext:
    """Rich personalized context for AI responses"""
    user_name: str
    greeting: str
    country: str
    country_context: Dict
    emotional_state: str
    emotional_history: List[Dict]
    emotional_trend: str
    family_members: List[Dict]
    key_memories: List[Dict]
    user_type: str  # expat, traveler, local
    learning_direction: str  # spanish, english
    proficiency_level: str
    total_messages: int
    streak_days: int
    context_string: str  # Ready-to-use for prompt


class EspaLuzPersonalization:
    """
    Builds rich personalized context for every response.
    No more "Hola, friend!" - uses real names and context.
    """
    
    def __init__(self, memory_instance):
        """
        Initialize with an EspaLuzMemory instance.
        
        Args:
            memory_instance: An initialized EspaLuzMemory object
        """
        self.memory = memory_instance
        self.user = memory_instance._user
        self.platform = memory_instance.platform
    
    def get_country_context(self, country: str = None) -> Dict:
        """Get country-specific greeting and context"""
        if not country:
            country = self.user.current_country
        
        if not country:
            return DEFAULT_COUNTRY
        
        # Normalize country name
        country_key = country.lower().replace(" ", "_").replace("-", "_")
        
        return COUNTRY_GREETINGS.get(country_key, DEFAULT_COUNTRY)
    
    def build_personalized_greeting(self, country: str = None, time_of_day: str = None) -> str:
        """Build a personalized greeting using user's name and country context"""
        user_name = self.user.display_name
        country_ctx = self.get_country_context(country)
        
        # Determine time-appropriate greeting
        if time_of_day is None:
            hour = datetime.now().hour
            if 5 <= hour < 12:
                time_of_day = "morning"
            elif 12 <= hour < 18:
                time_of_day = "afternoon"
            else:
                time_of_day = "evening"
        
        # Build greeting
        if user_name:
            if time_of_day == "morning":
                return f"¡Buenos días, {user_name}!"
            elif time_of_day == "afternoon":
                return f"¡Buenas tardes, {user_name}!"
            else:
                return f"¡Buenas noches, {user_name}!"
        else:
            # No name yet - use country casual greeting
            return f"{country_ctx['greeting']}!"
    
    def get_emotional_context(self) -> Dict:
        """Get emotional history and trend from database"""
        try:
            # Get last 7 days of emotional trend
            trend = self.memory.get_emotional_trend(days=7)
            recent_messages = self.memory.get_recent_messages(limit=5)
            
            # Determine dominant emotion
            if trend:
                dominant = max(trend.items(), key=lambda x: x[1]['count'])[0]
                avg_intensity = sum(e['intensity'] for e in trend.values()) / len(trend)
            else:
                dominant = "neutral"
                avg_intensity = 0.5
            
            # Determine trend direction
            if len(trend) >= 2:
                emotions_list = list(trend.keys())
                if emotions_list[-1] in ['happy', 'excited', 'grateful']:
                    trend_direction = "improving"
                elif emotions_list[-1] in ['frustrated', 'sad', 'anxious']:
                    trend_direction = "needs_support"
                else:
                    trend_direction = "stable"
            else:
                trend_direction = "new_user"
            
            return {
                "dominant_emotion": dominant,
                "avg_intensity": avg_intensity,
                "trend_direction": trend_direction,
                "history": trend,
                "recent_count": len(recent_messages)
            }
        except Exception as e:
            logger.warning(f"Error getting emotional context: {e}")
            return {
                "dominant_emotion": "neutral",
                "avg_intensity": 0.5,
                "trend_direction": "unknown",
                "history": {},
                "recent_count": 0
            }
    
    def get_family_context(self) -> List[Dict]:
        """Get family members for this user"""
        try:
            if self.user.family_id:
                return self.memory.get_family_members(self.user.family_id)
            return []
        except Exception as e:
            logger.warning(f"Error getting family context: {e}")
            return []
    
    def build_full_context(self, detected_country: str = None, current_emotion: str = None) -> PersonalizedContext:
        """
        Build complete personalized context for AI prompt.
        This is the MAIN function to call before generating a response.
        """
        # Get country context
        country = detected_country or self.user.current_country
        country_ctx = self.get_country_context(country)
        
        # Get emotional context from DB
        emotional_ctx = self.get_emotional_context()
        
        # Get family members
        family = self.get_family_context()
        
        # Get key memories
        try:
            memories = self.memory.get_user_memories(limit=10)
        except:
            memories = []
        
        # Build the context string for Claude
        context_parts = []
        
        # USER IDENTITY
        context_parts.append("=" * 50)
        context_parts.append("👤 USER PERSONALIZATION CONTEXT")
        context_parts.append("=" * 50)
        
        if self.user.display_name:
            context_parts.append(f"Name: {self.user.display_name}")
            context_parts.append(f"⚠️ ALWAYS address them as '{self.user.display_name}' - NEVER say 'friend' or 'amigo'!")
        else:
            context_parts.append("Name: Unknown (politely ask for their name!)")
            context_parts.append("⚠️ DO NOT say 'Hola, friend!' - Instead ask: '¿Cómo te llamas?' or 'What's your name?'")
        
        context_parts.append(f"User Type: {self.user.user_type}")
        context_parts.append(f"Learning: {self.user.learning_direction}")
        context_parts.append(f"Level: {self.user.proficiency_level}")
        context_parts.append(f"Messages: {self.user.total_messages}")
        context_parts.append(f"Platform: {self.platform}")
        
        # COUNTRY CONTEXT
        if country:
            context_parts.append("")
            context_parts.append("🌎 COUNTRY CONTEXT")
            context_parts.append(f"Country: {country.upper()}")
            context_parts.append(f"Local Greeting: {country_ctx['greeting']}")
            context_parts.append(f"Currency: {country_ctx['currency']}")
            context_parts.append(f"Timezone: {country_ctx['timezone']}")
            context_parts.append(f"Local Slang: {', '.join(country_ctx['slang'][:5])}")
            context_parts.append(f"Popular Topics: {', '.join(country_ctx['topics'][:5])}")
            context_parts.append(f"Local Flavor: {country_ctx['local_flavor']}")
            context_parts.append("⚠️ Use THIS country's Spanish variant, slang, and cultural references!")
        
        # EMOTIONAL CONTEXT
        context_parts.append("")
        context_parts.append("💝 EMOTIONAL CONTEXT (from database)")
        context_parts.append(f"Current Emotion: {current_emotion or emotional_ctx['dominant_emotion']}")
        context_parts.append(f"Recent Trend: {emotional_ctx['trend_direction']}")
        context_parts.append(f"Interaction Count: {emotional_ctx['recent_count']} recent messages")
        
        if emotional_ctx['trend_direction'] == "needs_support":
            context_parts.append("⚠️ User has been struggling - be extra supportive and encouraging!")
        elif emotional_ctx['trend_direction'] == "improving":
            context_parts.append("✨ User's mood is improving - maintain positive momentum!")
        
        # FAMILY CONTEXT
        if family:
            context_parts.append("")
            context_parts.append("👨‍👩‍👧‍👦 FAMILY CONTEXT")
            for member in family:
                context_parts.append(f"- {member.name} ({member.relationship}): {member.age_group}, Level: {member.proficiency_level}")
                if member.interests:
                    context_parts.append(f"  Interests: {', '.join(member.interests)}")
            context_parts.append("⚠️ Reference family members naturally: 'How's [name] doing with their Spanish?'")
        
        # KEY MEMORIES
        if memories:
            context_parts.append("")
            context_parts.append("🧠 KEY MEMORIES ABOUT THIS USER")
            for mem in memories[:5]:
                context_parts.append(f"- [{mem['memory_type']}] {mem['content']}")
            context_parts.append("⚠️ Reference these memories naturally in conversation!")
        
        # RESPONSE GUIDELINES
        context_parts.append("")
        context_parts.append("📝 PERSONALIZATION RULES")
        context_parts.append("1. Use the user's NAME in responses (not 'friend')")
        context_parts.append("2. Use country-specific Spanish variant and slang")
        context_parts.append("3. Reference emotional state appropriately")
        context_parts.append("4. Ask about family members if relevant")
        context_parts.append("5. Build on previous memories and context")
        context_parts.append("6. If no name, politely ask for it!")
        context_parts.append("=" * 50)
        
        context_string = "\n".join(context_parts)
        
        return PersonalizedContext(
            user_name=self.user.display_name or "",
            greeting=self.build_personalized_greeting(country),
            country=country or "unknown",
            country_context=country_ctx,
            emotional_state=current_emotion or emotional_ctx['dominant_emotion'],
            emotional_history=[],  # Summary in trend
            emotional_trend=emotional_ctx['trend_direction'],
            family_members=[{"name": m.name, "relationship": m.relationship} for m in family] if family else [],
            key_memories=[{"type": m['memory_type'], "content": m['content']} for m in memories],
            user_type=self.user.user_type,
            learning_direction=self.user.learning_direction,
            proficiency_level=self.user.proficiency_level,
            total_messages=self.user.total_messages,
            streak_days=self.user.streak_days,
            context_string=context_string
        )


# ============================================================================
# NAME EXTRACTION HELPERS
# ============================================================================

def extract_name_from_message(message: str) -> Optional[str]:
    """
    Try to extract a name from user's message.
    Handles: "I'm John", "My name is Maria", "Call me Alex", etc.
    """
    import re
    
    patterns = [
        r"(?:my name is|i'm|i am|call me|me llamo|soy)\s+([A-Z][a-z]+)",
        r"(?:this is|it's|es)\s+([A-Z][a-z]+)",
        r"^([A-Z][a-z]+)$",  # Just a name
    ]
    
    message_lower = message.lower()
    message_original = message
    
    for pattern in patterns:
        match = re.search(pattern, message_original, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Validate it looks like a name
            if len(name) >= 2 and len(name) <= 20 and name.isalpha():
                return name.title()
    
    return None


def extract_country_from_message(message: str) -> Optional[str]:
    """
    Try to extract a country from user's message.
    """
    message_lower = message.lower()
    
    # Check for explicit country mentions
    country_keywords = {
        "panama": "panama",
        "panamá": "panama",
        "costa rica": "costa_rica",
        "mexico": "mexico",
        "méxico": "mexico",
        "colombia": "colombia",
        "argentina": "argentina",
        "chile": "chile",
        "peru": "peru",
        "perú": "peru",
        "spain": "spain",
        "españa": "spain",
        "cuba": "cuba",
        "venezuela": "venezuela",
        "ecuador": "ecuador",
        "dominican": "dominican_republic",
        "puerto rico": "puerto_rico",
        "guatemala": "guatemala",
        "honduras": "honduras",
        "el salvador": "el_salvador",
        "nicaragua": "nicaragua",
        "bolivia": "bolivia",
        "uruguay": "uruguay",
        "paraguay": "paraguay",
        "equatorial guinea": "equatorial_guinea",
    }
    
    for keyword, country in country_keywords.items():
        if keyword in message_lower:
            return country
    
    return None


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("EspaLuz Personalization Engine Test")
    print("=" * 50)
    
    # Test country context
    for country in ["panama", "argentina", "mexico", "spain"]:
        ctx = COUNTRY_GREETINGS.get(country, DEFAULT_COUNTRY)
        print(f"\n{country.upper()}:")
        print(f"  Greeting: {ctx['greeting']}")
        print(f"  Slang: {', '.join(ctx['slang'][:3])}")
    
    # Test name extraction
    test_messages = [
        "My name is Elena",
        "I'm John",
        "Call me Alex",
        "Me llamo María",
        "Soy Carlos"
    ]
    print("\n\nName Extraction Tests:")
    for msg in test_messages:
        name = extract_name_from_message(msg)
        print(f"  '{msg}' → {name}")
    
    # Test country extraction
    test_countries = [
        "I live in Panama",
        "I'm from Argentina",
        "Visiting México next week"
    ]
    print("\nCountry Extraction Tests:")
    for msg in test_countries:
        country = extract_country_from_message(msg)
        print(f"  '{msg}' → {country}")
    
    print("\n✅ Personalization engine ready!")
