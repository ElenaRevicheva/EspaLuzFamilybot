"""
EspaLuz Enhancement Module - Makes ALL 8 Features Actually Work
================================================================
This module is ADDITIVE ONLY - it provides functions that return
context strings to be added to Claude prompts. It does NOT modify
any existing bot behavior.

Features:
1. Emotional Intelligence - Reads DB history, provides emotional context
2. Bilingual Mode - Supports English-for-Locals learning
3. 21 Country Contexts - All Spanish-speaking countries
4. User Type Modes - Expat, Traveler, Local
5. Relocation Assistance - Structured help
6. Emergency Features - SOS mode
7. Family Awareness - Uses family member data
8. Enhanced Memory - Cross-session recall

Author: CTO AIPA
Date: January 22, 2026
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# ============================================================================
# 1. EMOTIONAL INTELLIGENCE - Read from DB and provide context
# ============================================================================

def get_emotional_context_for_prompt(memory_instance) -> str:
    """
    Get emotional history from database and format it for Claude's prompt.
    This makes the bot ACTUALLY remember past emotions.
    """
    try:
        # Get emotional trend from last 7 days
        trend = memory_instance.get_emotional_trend(days=7)
        
        if not trend:
            return ""
        
        # Find dominant emotion
        dominant = max(trend.items(), key=lambda x: x[1]['count'])[0] if trend else "neutral"
        
        # Build context
        context = f"""
🧠 EMOTIONAL MEMORY (from database - last 7 days):
- Dominant emotion: {dominant.upper()}
- Emotional pattern: {', '.join(trend.keys())}
"""
        
        # Add specific guidance based on emotional state
        if dominant in ['frustrated', 'confused', 'anxious']:
            context += """
⚠️ User has been struggling recently. Be EXTRA supportive:
- Simplify explanations
- Celebrate small wins
- Offer encouragement
- Ask if they need a break
"""
        elif dominant in ['happy', 'excited', 'confident']:
            context += """
✨ User is in a positive state! Maintain momentum:
- Challenge them slightly more
- Introduce new vocabulary
- Keep the energy high
"""
        elif dominant in ['sad', 'homesick', 'lonely']:
            context += """
💙 User may be feeling down. Be warm and supportive:
- Be empathetic and understanding
- Relate to expat challenges
- Suggest community connections
"""
        
        return context
        
    except Exception as e:
        logger.warning(f"Could not get emotional context: {e}")
        return ""


# ============================================================================
# 2. BILINGUAL MODE - English for Locals
# ============================================================================

LEARNING_MODES = {
    "spanish": {
        "name": "Spanish Learning",
        "target_language": "Spanish",
        "native_language": "English",
        "greeting": "¡Hola",
        "description": "Learning Spanish as a second language"
    },
    "english": {
        "name": "English Learning", 
        "target_language": "English",
        "native_language": "Spanish",
        "greeting": "Hello",
        "description": "Learning English as a second language"
    }
}

def get_learning_direction_context(user_type: str, learning_direction: str) -> str:
    """
    Get context for the user's learning direction.
    Supports BOTH Spanish-for-Expats AND English-for-Locals.
    """
    if learning_direction == "english" or user_type == "local":
        return """
🎯 ENGLISH LEARNING MODE (for Spanish speakers/locals):
- User is a native Spanish speaker learning English
- Explain English concepts using Spanish comparisons
- Use Spanish for clarifications when needed
- Focus on: Service industry phrases, travel English, business English
- Common goals: Better tips, career advancement, travel abroad

Example approach:
- "En inglés, decimos 'How can I help you?' que es como '¿Cómo puedo ayudarte?'"
- "The English 'th' sound doesn't exist in Spanish - practice with 'the', 'this', 'that'"

Key phrases for service workers:
- "How may I help you?" / "¿En qué puedo ayudarle?"
- "Your total is..." / "Su total es..."
- "Have a nice day!" / "¡Que tenga un buen día!"
"""
    else:
        return """
🎯 SPANISH LEARNING MODE (for English speakers/expats):
- User is learning Spanish as a second language
- Use English for explanations when helpful
- Focus on practical, everyday Spanish
- Adapt to their proficiency level
"""


# ============================================================================
# 3. ALL 21 SPANISH-SPEAKING COUNTRY CONTEXTS
# ============================================================================

COUNTRY_CONTEXTS_FULL = {
    # CENTRAL AMERICA
    "panama": {
        "flag": "🇵🇦",
        "greeting": "¡Qué xopa!",
        "slang": ["xopa", "fren", "pela'o", "chombo", "yeye", "juega vivo"],
        "currency": "Balboa/USD",
        "topics": ["Canal", "Casco Viejo", "Bocas del Toro", "sancocho", "ceviche", "Carnival"],
        "relocation": {
            "popular_areas": ["Panama City", "Boquete", "Coronado", "Pedasi"],
            "schools": ["International School of Panama", "Balboa Academy", "King's College"],
            "visa_types": ["Friendly Nations Visa", "Pensionado", "Digital Nomad"],
            "cost_of_living": "Medium-High in city, Lower in countryside"
        },
        "emergency": {
            "police": "104",
            "ambulance": "911",
            "fire": "103",
            "us_embassy": "+507-317-5000"
        }
    },
    "costa_rica": {
        "flag": "🇨🇷",
        "greeting": "¡Pura vida!",
        "slang": ["pura vida", "mae", "tuanis", "tico/a", "chunche", "birra"],
        "currency": "Colón (CRC)",
        "topics": ["playas", "volcanes", "biodiversidad", "gallo pinto", "café"],
        "relocation": {
            "popular_areas": ["San José", "Guanacaste", "Puerto Viejo", "Monteverde"],
            "schools": ["Country Day School", "Lincoln School", "Blue Valley"],
            "visa_types": ["Rentista", "Pensionado", "Digital Nomad"],
            "cost_of_living": "Medium-High"
        },
        "emergency": {"police": "911", "ambulance": "911", "us_embassy": "+506-2519-2000"}
    },
    "mexico": {
        "flag": "🇲🇽",
        "greeting": "¡Qué onda!",
        "slang": ["güey/wey", "chido", "neta", "órale", "chamba", "padre", "no manches"],
        "currency": "Peso Mexicano (MXN)",
        "topics": ["tacos", "tequila", "mariachi", "CDMX", "playas", "pirámides"],
        "relocation": {
            "popular_areas": ["Mexico City", "Playa del Carmen", "San Miguel de Allende", "Mérida", "Puerto Vallarta"],
            "schools": ["American School Foundation", "Greengates", "Westhill"],
            "visa_types": ["Temporary Resident", "Permanent Resident"],
            "cost_of_living": "Low-Medium"
        },
        "emergency": {"police": "911", "ambulance": "911", "us_embassy": "+52-55-5080-2000"}
    },
    "guatemala": {
        "flag": "🇬🇹",
        "greeting": "¡Qué onda!",
        "slang": ["qué onda", "canche", "patojo", "chilero", "shuco", "chapin"],
        "currency": "Quetzal (GTQ)",
        "topics": ["Antigua", "Tikal", "volcanes", "textiles", "tamales", "Maya"],
        "relocation": {
            "popular_areas": ["Antigua", "Guatemala City", "Lake Atitlán"],
            "schools": ["American School of Guatemala", "Colegio Maya"],
            "visa_types": ["Tourist (extendable)", "Temporary Resident"],
            "cost_of_living": "Low"
        },
        "emergency": {"police": "110", "ambulance": "128", "us_embassy": "+502-2326-4000"}
    },
    "honduras": {
        "flag": "🇭🇳",
        "greeting": "¡Qué ondas!",
        "slang": ["maje", "catracho", "cipote", "alero", "cheque"],
        "currency": "Lempira (HNL)",
        "topics": ["Copán", "Roatán", "baleadas", "café", "mariscos"],
        "relocation": {
            "popular_areas": ["Tegucigalpa", "Roatán", "San Pedro Sula"],
            "schools": ["American School Tegucigalpa", "Discovery School"],
            "visa_types": ["Tourist", "Resident"],
            "cost_of_living": "Low"
        },
        "emergency": {"police": "199", "ambulance": "195", "us_embassy": "+504-2236-9320"}
    },
    "el_salvador": {
        "flag": "🇸🇻",
        "greeting": "¡Qué onda!",
        "slang": ["chivo", "bicho", "cipote", "chucho", "guanaco"],
        "currency": "USD",
        "topics": ["pupusas", "playas", "volcanes", "Bitcoin", "artesanías"],
        "relocation": {
            "popular_areas": ["San Salvador", "El Tunco", "Santa Ana"],
            "schools": ["American School of El Salvador", "Escuela Americana"],
            "visa_types": ["Tourist", "Temporary Resident"],
            "cost_of_living": "Low"
        },
        "emergency": {"police": "911", "ambulance": "911", "us_embassy": "+503-2501-2999"}
    },
    "nicaragua": {
        "flag": "🇳🇮",
        "greeting": "¡Qué onda!",
        "slang": ["tuani", "nica", "maje", "chunche", "pinolero"],
        "currency": "Córdoba (NIO)",
        "topics": ["Granada", "León", "volcanes", "gallo pinto", "poesía"],
        "relocation": {
            "popular_areas": ["Granada", "San Juan del Sur", "León"],
            "schools": ["American Nicaraguan School", "Lincoln International"],
            "visa_types": ["Tourist", "Resident"],
            "cost_of_living": "Very Low"
        },
        "emergency": {"police": "118", "ambulance": "128", "us_embassy": "+505-2252-7100"}
    },
    
    # CARIBBEAN
    "cuba": {
        "flag": "🇨🇺",
        "greeting": "¡Oye, qué bolá!",
        "slang": ["qué bolá", "asere", "yuma", "guagua", "fula", "paladar"],
        "currency": "Peso Cubano (CUP)",
        "topics": ["salsa", "Habana Vieja", "mojitos", "béisbol", "carros clásicos"],
        "relocation": {"popular_areas": ["Havana", "Varadero"], "cost_of_living": "Complex system"},
        "emergency": {"police": "106", "ambulance": "104"}
    },
    "dominican_republic": {
        "flag": "🇩🇴",
        "greeting": "¡Klk! (Qué lo que)",
        "slang": ["klk", "tato", "vaina", "tigueraje", "jevi", "dique"],
        "currency": "Peso Dominicano (DOP)",
        "topics": ["merengue", "bachata", "playas", "mangú", "béisbol"],
        "relocation": {
            "popular_areas": ["Santo Domingo", "Punta Cana", "Santiago", "Las Terrenas"],
            "schools": ["Carol Morgan School", "American School of Santo Domingo"],
            "visa_types": ["Tourist", "Residency"],
            "cost_of_living": "Low-Medium"
        },
        "emergency": {"police": "911", "ambulance": "911", "us_embassy": "+1-809-567-7775"}
    },
    "puerto_rico": {
        "flag": "🇵🇷",
        "greeting": "¡Wepa!",
        "slang": ["wepa", "brutal", "chavos", "janguear", "corillo", "boricua"],
        "currency": "USD",
        "topics": ["reggaetón", "Old San Juan", "mofongo", "playas", "El Yunque"],
        "relocation": {
            "popular_areas": ["San Juan", "Rincón", "Dorado"],
            "schools": ["American Military Academy", "Baldwin School"],
            "visa_types": ["US Territory - no visa needed for US citizens"],
            "cost_of_living": "Medium-High"
        },
        "emergency": {"police": "911", "ambulance": "911"}
    },
    
    # SOUTH AMERICA
    "colombia": {
        "flag": "🇨🇴",
        "greeting": "¡Quiubo!",
        "slang": ["parcero/parce", "bacano", "chévere", "berraco", "qué más", "listo"],
        "currency": "Peso Colombiano (COP)",
        "topics": ["café", "Cartagena", "Medellín", "arepas", "cumbia", "salsa"],
        "relocation": {
            "popular_areas": ["Medellín", "Bogotá", "Cartagena", "Cali", "Santa Marta"],
            "schools": ["Colegio Nueva Granada", "Colegio Anglo Colombiano"],
            "visa_types": ["Digital Nomad Visa", "Resident Visa", "M Visa"],
            "cost_of_living": "Low-Medium"
        },
        "emergency": {"police": "123", "ambulance": "123", "us_embassy": "+57-1-275-2000"}
    },
    "venezuela": {
        "flag": "🇻🇪",
        "greeting": "¡Épale!",
        "slang": ["pana", "chévere", "fino", "marico", "arrecho", "burda"],
        "currency": "Bolívar (VES)",
        "topics": ["arepas", "Salto Ángel", "béisbol", "hallacas", "playas"],
        "relocation": {"popular_areas": ["Caracas", "Margarita"], "cost_of_living": "Complex"},
        "emergency": {"police": "171", "ambulance": "171"}
    },
    "ecuador": {
        "flag": "🇪🇨",
        "greeting": "¡Qué más!",
        "slang": ["ñaño/a", "chuchaqui", "bacán", "simon", "nel"],
        "currency": "USD",
        "topics": ["Galápagos", "Quito", "ceviche", "sombreros", "volcanes", "Cuenca"],
        "relocation": {
            "popular_areas": ["Cuenca", "Quito", "Guayaquil", "Vilcabamba"],
            "schools": ["Colegio Americano de Quito", "Academia Cotopaxi"],
            "visa_types": ["Professional Visa", "Investor Visa", "Retirement Visa"],
            "cost_of_living": "Low"
        },
        "emergency": {"police": "911", "ambulance": "911", "us_embassy": "+593-2-398-5000"}
    },
    "peru": {
        "flag": "🇵🇪",
        "greeting": "¡Habla!",
        "slang": ["causa", "pata", "chévere", "jato", "bravazo", "al toque"],
        "currency": "Sol (PEN)",
        "topics": ["ceviche", "Machu Picchu", "pisco", "Lima", "quinoa", "Cusco"],
        "relocation": {
            "popular_areas": ["Lima", "Cusco", "Arequipa", "Miraflores"],
            "schools": ["American School of Lima", "Markham College"],
            "visa_types": ["Tourist", "Work Visa", "Resident Visa"],
            "cost_of_living": "Low-Medium"
        },
        "emergency": {"police": "105", "ambulance": "117", "us_embassy": "+51-1-618-2000"}
    },
    "bolivia": {
        "flag": "🇧🇴",
        "greeting": "¡Qué tal!",
        "slang": ["yapa", "chango", "jailón", "polera", "trufi"],
        "currency": "Boliviano (BOB)",
        "topics": ["Salar de Uyuni", "La Paz", "cholitas", "salteñas", "Carnaval"],
        "relocation": {
            "popular_areas": ["La Paz", "Santa Cruz", "Cochabamba", "Sucre"],
            "schools": ["American Cooperative School", "Santa Cruz Cooperative School"],
            "visa_types": ["Tourist", "Specific Purpose Visa"],
            "cost_of_living": "Very Low"
        },
        "emergency": {"police": "110", "ambulance": "118", "us_embassy": "+591-2-216-8000"}
    },
    "chile": {
        "flag": "🇨🇱",
        "greeting": "¡Hola po!",
        "slang": ["po", "weón/weona", "cachai", "fome", "bacán", "al tiro"],
        "currency": "Peso Chileno (CLP)",
        "topics": ["vino", "Patagonia", "Atacama", "empanadas", "pisco", "Santiago"],
        "relocation": {
            "popular_areas": ["Santiago", "Valparaíso", "Viña del Mar", "Puerto Varas"],
            "schools": ["Nido de Águilas", "Santiago College", "The Grange"],
            "visa_types": ["Tourist", "Temporary Resident", "Work Visa"],
            "cost_of_living": "Medium-High"
        },
        "emergency": {"police": "133", "ambulance": "131", "us_embassy": "+56-2-2330-3000"}
    },
    "argentina": {
        "flag": "🇦🇷",
        "greeting": "¡Che, qué onda!",
        "slang": ["che", "boludo/a", "bárbaro", "quilombo", "morfar", "laburo", "bondi"],
        "currency": "Peso Argentino (ARS)",
        "topics": ["tango", "asado", "fútbol", "mate", "Buenos Aires", "Messi"],
        "relocation": {
            "popular_areas": ["Buenos Aires", "Mendoza", "Bariloche", "Córdoba"],
            "schools": ["Lincoln School", "St. Andrew's Scots School", "American Community School"],
            "visa_types": ["Tourist (extendable)", "Temporary Resident", "Rentista"],
            "cost_of_living": "Low (due to exchange rate)"
        },
        "emergency": {"police": "911", "ambulance": "107", "us_embassy": "+54-11-5777-4533"}
    },
    "uruguay": {
        "flag": "🇺🇾",
        "greeting": "¡Bo, qué hacés!",
        "slang": ["bo", "ta", "championes", "celeste", "gurí", "botija"],
        "currency": "Peso Uruguayo (UYU)",
        "topics": ["mate", "asado", "fútbol", "Punta del Este", "candombe"],
        "relocation": {
            "popular_areas": ["Montevideo", "Punta del Este", "Colonia"],
            "schools": ["Uruguayan American School", "British Schools"],
            "visa_types": ["Tourist", "Temporary Resident", "Retirement Visa"],
            "cost_of_living": "Medium"
        },
        "emergency": {"police": "911", "ambulance": "911", "us_embassy": "+598-1770-2000"}
    },
    "paraguay": {
        "flag": "🇵🇾",
        "greeting": "¡Mba'éichapa! (Guaraní)",
        "slang": ["che", "mita'i", "kuña", "karai", "guapo"],
        "currency": "Guaraní (PYG)",
        "topics": ["tereré", "chipa", "Guaraní", "arpa", "Itaipú"],
        "relocation": {
            "popular_areas": ["Asunción", "Encarnación", "Ciudad del Este"],
            "schools": ["American School of Asunción", "Goethe Schule"],
            "visa_types": ["Tourist", "Temporary Resident"],
            "cost_of_living": "Very Low"
        },
        "emergency": {"police": "911", "ambulance": "911", "us_embassy": "+595-21-213-715"}
    },
    
    # EUROPE
    "spain": {
        "flag": "🇪🇸",
        "greeting": "¡Hola, qué tal!",
        "slang": ["tío/tía", "mola", "guay", "currar", "flipar", "quedamos"],
        "currency": "Euro (EUR)",
        "topics": ["tapas", "paella", "fútbol", "flamenco", "Madrid", "Barcelona", "siesta"],
        "relocation": {
            "popular_areas": ["Madrid", "Barcelona", "Valencia", "Málaga", "Seville"],
            "schools": ["American School of Madrid", "American School of Barcelona"],
            "visa_types": ["Non-Lucrative Visa", "Digital Nomad Visa", "Golden Visa"],
            "cost_of_living": "Medium-High (varies by city)"
        },
        "emergency": {"police": "091", "ambulance": "112", "us_embassy": "+34-91-587-2200"}
    },
    
    # AFRICA
    "equatorial_guinea": {
        "flag": "🇬🇶",
        "greeting": "¡Hola!",
        "slang": ["compa", "eah", "hermano"],
        "currency": "Franco CFA (XAF)",
        "topics": ["petróleo", "selva", "Malabo", "Bioko", "cultura Fang"],
        "relocation": {"popular_areas": ["Malabo", "Bata"], "cost_of_living": "High"},
        "emergency": {"police": "114", "ambulance": "115"}
    }
}

def get_country_context_full(country: str) -> str:
    """Get comprehensive country context for Claude's prompt."""
    country_key = country.lower().replace(" ", "_").replace("-", "_")
    
    ctx = COUNTRY_CONTEXTS_FULL.get(country_key)
    if not ctx:
        return f"Country: {country} (no specific context available)"
    
    context = f"""
🌎 COUNTRY CONTEXT: {country.upper()} {ctx['flag']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Local greeting: "{ctx['greeting']}"
Currency: {ctx['currency']}
Local slang to teach: {', '.join(ctx['slang'][:5])}
Popular topics: {', '.join(ctx['topics'][:5])}

USE THIS COUNTRY'S:
- Specific slang and expressions
- Cultural references
- Local topics and examples
"""
    
    return context


# ============================================================================
# 4. USER TYPE MODES - Expat, Traveler, Local
# ============================================================================

def get_user_type_context(user_type: str) -> str:
    """Get context based on user type."""
    
    if user_type == "traveler":
        return """
🧳 TRAVELER MODE ACTIVATED:
- User is traveling, needs QUICK help
- Focus on: Immediate, practical phrases
- Priorities: Ordering food, directions, emergencies, prices
- Keep responses SHORT and actionable
- Include pronunciation guides
- Emergency phrases are HIGH priority

Quick Travel Phrases:
- "¿Cuánto cuesta?" = How much?
- "¿Dónde está...?" = Where is...?
- "La cuenta, por favor" = The check, please
- "Necesito ayuda" = I need help
"""
    
    elif user_type == "local":
        return """
🏠 LOCAL MODE - ENGLISH LEARNING:
- User is a native Spanish speaker
- They want to learn ENGLISH
- Goals: Better service job, travel abroad, communicate with tourists
- Use Spanish to explain English concepts
- Focus on: Service phrases, tips vocabulary, travel English

Explain English using Spanish:
- Use cognates when possible
- Compare grammar structures
- Help with English pronunciation
- Focus on practical workplace English
"""
    
    else:  # expat (default)
        return """
🏡 EXPAT/FAMILY MODE:
- User is living abroad long-term
- Needs: Deep cultural integration
- Focus on: Daily life vocabulary, making friends, navigating systems
- Include: Cultural insights, local customs, expat tips
- Remember: They're building a life here, not just visiting
"""


# ============================================================================
# 5. RELOCATION ASSISTANCE
# ============================================================================

def get_relocation_context(country: str, topic: str = None) -> str:
    """Get structured relocation assistance for a country."""
    country_key = country.lower().replace(" ", "_")
    ctx = COUNTRY_CONTEXTS_FULL.get(country_key, {})
    reloc = ctx.get("relocation", {})
    
    if not reloc:
        return ""
    
    context = f"""
📍 RELOCATION INFO FOR {country.upper()}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Popular expat areas: {', '.join(reloc.get('popular_areas', ['Ask locally']))}
International schools: {', '.join(reloc.get('schools', ['Research needed'])[:3])}
Visa options: {', '.join(reloc.get('visa_types', ['Check embassy'])[:3])}
Cost of living: {reloc.get('cost_of_living', 'Varies')}

When discussing relocation:
- Be specific to THIS country
- Mention these actual schools/areas
- Reference real visa types
- Give practical, actionable advice
"""
    return context


# ============================================================================
# 6. EMERGENCY FEATURES
# ============================================================================

def get_emergency_context(country: str) -> str:
    """Get emergency information for a country."""
    country_key = country.lower().replace(" ", "_")
    ctx = COUNTRY_CONTEXTS_FULL.get(country_key, {})
    emergency = ctx.get("emergency", {})
    
    if not emergency:
        return "For emergencies, call the local emergency number (often 911) or contact your embassy."
    
    context = f"""
🆘 EMERGENCY INFO FOR {country.upper()}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Police: {emergency.get('police', 'Unknown')}
Ambulance: {emergency.get('ambulance', 'Unknown')}
Fire: {emergency.get('fire', emergency.get('ambulance', 'Unknown'))}
US Embassy: {emergency.get('us_embassy', 'Look up online')}

CRITICAL EMERGENCY PHRASES:
- "¡Ayuda!" = Help!
- "¡Llame a la policía!" = Call the police!
- "¡Necesito un médico!" = I need a doctor!
- "¡Es una emergencia!" = It's an emergency!
- "Soy estadounidense/británico" = I'm American/British
"""
    return context


def is_emergency_message(message: str) -> bool:
    """Detect if a message is about an emergency."""
    emergency_keywords = [
        "emergency", "emergencia", "help", "ayuda", "sos", "911",
        "police", "policía", "hospital", "doctor", "médico",
        "accident", "accidente", "robbery", "robo", "stolen",
        "lost passport", "pasaporte perdido", "embassy", "embajada",
        "danger", "peligro", "hurt", "herido", "sick", "enfermo"
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in emergency_keywords)


# ============================================================================
# 7. FAMILY AWARENESS
# ============================================================================

def get_family_context(memory_instance) -> str:
    """Get family member context from database."""
    try:
        user = memory_instance._user
        if not user.family_id:
            return ""
        
        family_members = memory_instance.get_family_members(user.family_id)
        if not family_members:
            return ""
        
        context = """
👨‍👩‍👧‍👦 FAMILY CONTEXT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for member in family_members:
            context += f"- {member.name}"
            if member.relationship:
                context += f" ({member.relationship})"
            if member.age_group:
                context += f" - {member.age_group}"
            if member.proficiency_level:
                context += f" - Level: {member.proficiency_level}"
            context += "\n"
        
        context += """
⚠️ FAMILY AWARENESS RULES:
- Ask about family members by NAME
- "How is [name] doing with their Spanish?"
- Suggest family learning activities
- Remember each member's level
"""
        return context
        
    except Exception as e:
        logger.warning(f"Could not get family context: {e}")
        return ""


# ============================================================================
# 8. ENHANCED MEMORY - Cross-session recall
# ============================================================================

def get_memory_context(memory_instance) -> str:
    """Get key memories about the user for context."""
    try:
        memories = memory_instance.get_user_memories(limit=10)
        if not memories:
            return ""
        
        context = """
🧠 KEY MEMORIES ABOUT THIS USER:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for mem in memories[:5]:
            context += f"- [{mem['memory_type']}] {mem['content']}\n"
        
        context += """
⚠️ USE THESE MEMORIES:
- Reference them naturally in conversation
- "I remember you mentioned..."
- Build on past conversations
- Show you actually remember them
"""
        return context
        
    except Exception as e:
        logger.warning(f"Could not get memory context: {e}")
        return ""


# ============================================================================
# MASTER FUNCTION - Combine all contexts
# ============================================================================

def build_enhanced_context(
    memory_instance,
    user_type: str = "expat",
    country: str = "panama",
    learning_direction: str = "spanish",
    current_message: str = ""
) -> str:
    """
    Build complete enhanced context for Claude's prompt.
    This combines ALL 8 features into one context string.
    """
    
    parts = []
    
    # 1. Emotional Intelligence
    emotional = get_emotional_context_for_prompt(memory_instance)
    if emotional:
        parts.append(emotional)
    
    # 2. Learning Direction (Spanish or English)
    learning = get_learning_direction_context(user_type, learning_direction)
    parts.append(learning)
    
    # 3. Country Context
    country_ctx = get_country_context_full(country)
    parts.append(country_ctx)
    
    # 4. User Type Mode
    user_mode = get_user_type_context(user_type)
    parts.append(user_mode)
    
    # 5. Relocation (if relevant)
    if any(word in current_message.lower() for word in ['school', 'apartment', 'visa', 'job', 'move', 'relocat']):
        reloc = get_relocation_context(country)
        if reloc:
            parts.append(reloc)
    
    # 6. Emergency (if relevant)
    if is_emergency_message(current_message):
        emergency = get_emergency_context(country)
        parts.append(emergency)
        parts.append("\n⚠️ THIS IS AN EMERGENCY - Prioritize safety information!")
    
    # 7. Family Context
    family = get_family_context(memory_instance)
    if family:
        parts.append(family)
    
    # 8. Memory Context
    memories = get_memory_context(memory_instance)
    if memories:
        parts.append(memories)
    
    return "\n".join(parts)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("EspaLuz Enhancements Module")
    print("=" * 50)
    
    # Test country contexts
    print("\n📍 Countries available:", len(COUNTRY_CONTEXTS_FULL))
    for country in COUNTRY_CONTEXTS_FULL.keys():
        ctx = COUNTRY_CONTEXTS_FULL[country]
        print(f"  {ctx['flag']} {country}: {ctx['greeting']}")
    
    # Test emergency detection
    test_messages = [
        "I need help!",
        "Where is the hospital?",
        "How do you say hello?",
        "My passport was stolen!"
    ]
    print("\n🆘 Emergency detection:")
    for msg in test_messages:
        print(f"  '{msg}' → Emergency: {is_emergency_message(msg)}")
    
    print("\n✅ Module ready for integration!")
