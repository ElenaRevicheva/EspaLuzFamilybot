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
        # Get emotional trend from last 7 days.
        # EspaLuzMemory.get_emotional_trend(user_id, days=7) REQUIRES user_id —
        # calling it with days= only raised TypeError on every message, which the
        # caller swallowed, so emotional memory never reached the prompt.
        uid = getattr(memory_instance, "user_id", None)
        if not uid:
            return ""
        trend = memory_instance.get_emotional_trend(uid, days=7)

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
        "slang": {"xopa": "what's up", "fren": "friend/buddy", "pela'o": "broke/no money", "chombo": "Afro-Panamanian (can be offensive)", "yeye": "fancy/posh", "juega vivo": "be street smart"},
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
            "us_embassy": ["507", "317", "5000"]
        }
    },
    "costa_rica": {
        "flag": "🇨🇷",
        "greeting": "¡Pura vida!",
        "slang": {"pura vida": "awesome/great/hello/goodbye (universal)", "mae": "dude/bro", "tuanis": "cool/nice", "tico/a": "Costa Rican person", "chunche": "thing/stuff", "birra": "beer"},
        "currency": "Colón (CRC)",
        "topics": ["playas", "volcanes", "biodiversidad", "gallo pinto", "café"],
        "relocation": {
            "popular_areas": ["San José", "Guanacaste", "Puerto Viejo", "Monteverde"],
            "schools": ["Country Day School", "Lincoln School", "Blue Valley"],
            "visa_types": ["Rentista", "Pensionado", "Digital Nomad"],
            "cost_of_living": "Medium-High"
        },
        "emergency": {"police": "911", "ambulance": "911", "us_embassy": ["506", "2519", "2000"]}
    },
    "mexico": {
        "flag": "🇲🇽",
        "greeting": "¡Qué onda!",
        "slang": {"güey/wey": "dude/bro", "chido": "cool/awesome", "neta": "really?/truth", "órale": "wow/ok/let's go", "chamba": "work/job", "padre": "cool/great", "no manches": "no way!/you're kidding"},
        "currency": "Peso Mexicano (MXN)",
        "topics": ["tacos", "tequila", "mariachi", "CDMX", "playas", "pirámides"],
        "relocation": {
            "popular_areas": ["Mexico City", "Playa del Carmen", "San Miguel de Allende", "Mérida", "Puerto Vallarta"],
            "schools": ["American School Foundation", "Greengates", "Westhill"],
            "visa_types": ["Temporary Resident", "Permanent Resident"],
            "cost_of_living": "Low-Medium"
        },
        "emergency": {"police": "911", "ambulance": "911", "us_embassy": ["52", "55", "5080", "2000"]}
    },
    "guatemala": {
        "flag": "🇬🇹",
        "greeting": "¡Qué onda!",
        "slang": {"qué onda": "what's up", "canche": "blonde person", "patojo": "kid/young person", "chilero": "cool/nice", "shuco": "dirty hot dog (street food)", "chapin": "Guatemalan person"},
        "currency": "Quetzal (GTQ)",
        "topics": ["Antigua", "Tikal", "volcanes", "textiles", "tamales", "Maya"],
        "relocation": {
            "popular_areas": ["Antigua", "Guatemala City", "Lake Atitlán"],
            "schools": ["American School of Guatemala", "Colegio Maya"],
            "visa_types": ["Tourist (extendable)", "Temporary Resident"],
            "cost_of_living": "Low"
        },
        "emergency": {"police": "110", "ambulance": "128", "us_embassy": ["502", "2326", "4000"]}
    },
    "honduras": {
        "flag": "🇭🇳",
        "greeting": "¡Qué ondas!",
        "slang": {"maje": "dude/buddy", "catracho": "Honduran person", "cipote": "kid/child", "alero": "close friend", "cheque": "ok/sure"},
        "currency": "Lempira (HNL)",
        "topics": ["Copán", "Roatán", "baleadas", "café", "mariscos"],
        "relocation": {
            "popular_areas": ["Tegucigalpa", "Roatán", "San Pedro Sula"],
            "schools": ["American School Tegucigalpa", "Discovery School"],
            "visa_types": ["Tourist", "Resident"],
            "cost_of_living": "Low"
        },
        "emergency": {"police": "199", "ambulance": "195", "us_embassy": ["504", "2236", "9320"]}
    },
    "el_salvador": {
        "flag": "🇸🇻",
        "greeting": "¡Qué onda!",
        "slang": {"chivo": "cool/awesome", "bicho": "kid/dude", "cipote": "kid/child", "chucho": "dog/stingy person", "guanaco": "Salvadoran person"},
        "currency": "USD",
        "topics": ["pupusas", "playas", "volcanes", "Bitcoin", "artesanías"],
        "relocation": {
            "popular_areas": ["San Salvador", "El Tunco", "Santa Ana"],
            "schools": ["American School of El Salvador", "Escuela Americana"],
            "visa_types": ["Tourist", "Temporary Resident"],
            "cost_of_living": "Low"
        },
        "emergency": {"police": "911", "ambulance": "911", "us_embassy": ["503", "2501", "2999"]}
    },
    "nicaragua": {
        "flag": "🇳🇮",
        "greeting": "¡Qué onda!",
        "slang": {"tuani": "cool/great", "nica": "Nicaraguan person", "maje": "dude/buddy", "chunche": "thing/stuff", "pinolero": "Nicaraguan (from pinol drink)"},
        "currency": "Córdoba (NIO)",
        "topics": ["Granada", "León", "volcanes", "gallo pinto", "poesía"],
        "relocation": {
            "popular_areas": ["Granada", "San Juan del Sur", "León"],
            "schools": ["American Nicaraguan School", "Lincoln International"],
            "visa_types": ["Tourist", "Resident"],
            "cost_of_living": "Very Low"
        },
        "emergency": {"police": "118", "ambulance": "128", "us_embassy": ["505", "2252", "7100"]}
    },
    
    # CARIBBEAN
    "cuba": {
        "flag": "🇨🇺",
        "greeting": "¡Oye, qué bolá!",
        "slang": {"qué bolá": "what's up", "asere": "friend/buddy", "yuma": "foreigner/American", "guagua": "bus", "fula": "dollar/money", "paladar": "private restaurant"},
        "currency": "Peso Cubano (CUP)",
        "topics": ["salsa", "Habana Vieja", "mojitos", "béisbol", "carros clásicos"],
        "relocation": {"popular_areas": ["Havana", "Varadero"], "cost_of_living": "Complex system"},
        "emergency": {"police": "106", "ambulance": "104"}
    },
    "dominican_republic": {
        "flag": "🇩🇴",
        "greeting": "¡Klk! (Qué lo que)",
        "slang": {"klk": "what's up (qué lo qué)", "tato": "ok/sure", "vaina": "thing/stuff/situation", "tigueraje": "street smarts/hustle", "jevi": "cool/heavy (from English)", "dique": "supposedly/apparently"},
        "currency": "Peso Dominicano (DOP)",
        "topics": ["merengue", "bachata", "playas", "mangú", "béisbol"],
        "relocation": {
            "popular_areas": ["Santo Domingo", "Punta Cana", "Santiago", "Las Terrenas"],
            "schools": ["Carol Morgan School", "American School of Santo Domingo"],
            "visa_types": ["Tourist", "Residency"],
            "cost_of_living": "Low-Medium"
        },
        "emergency": {"police": "911", "ambulance": "911", "us_embassy": ["1", "809", "567", "7775"]}
    },
    "puerto_rico": {
        "flag": "🇵🇷",
        "greeting": "¡Wepa!",
        "slang": {"wepa": "wow!/yay!", "brutal": "awesome/amazing", "chavos": "money", "janguear": "hang out", "corillo": "friend group/crew", "boricua": "Puerto Rican person"},
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
        "slang": {"parcero/parce": "buddy/friend", "bacano": "cool/awesome", "chévere": "great/nice", "berraco": "awesome/badass (or angry)", "qué más": "what's up", "listo": "ok/ready/smart"},
        "currency": "Peso Colombiano (COP)",
        "topics": ["café", "Cartagena", "Medellín", "arepas", "cumbia", "salsa"],
        "relocation": {
            "popular_areas": ["Medellín", "Bogotá", "Cartagena", "Cali", "Santa Marta"],
            "schools": ["Colegio Nueva Granada", "Colegio Anglo Colombiano"],
            "visa_types": ["Digital Nomad Visa", "Resident Visa", "M Visa"],
            "cost_of_living": "Low-Medium"
        },
        "emergency": {"police": "123", "ambulance": "123", "us_embassy": ["57", "1", "275", "2000"]}
    },
    "venezuela": {
        "flag": "🇻🇪",
        "greeting": "¡Épale!",
        "slang": {"pana": "friend/buddy", "chévere": "cool/great", "fino": "great/perfect", "marico": "dude (casual, can be vulgar)", "arrecho": "angry/awesome", "burda": "a lot/very much"},
        "currency": "Bolívar (VES)",
        "topics": ["arepas", "Salto Ángel", "béisbol", "hallacas", "playas"],
        "relocation": {"popular_areas": ["Caracas", "Margarita"], "cost_of_living": "Complex"},
        "emergency": {"police": "171", "ambulance": "171"}
    },
    "ecuador": {
        "flag": "🇪🇨",
        "greeting": "¡Qué más!",
        "slang": {"ñaño/a": "brother/sister/friend", "chuchaqui": "hangover", "bacán": "cool/awesome", "simon": "yes/yeah", "nel": "no/nope"},
        "currency": "USD",
        "topics": ["Galápagos", "Quito", "ceviche", "sombreros", "volcanes", "Cuenca"],
        "relocation": {
            "popular_areas": ["Cuenca", "Quito", "Guayaquil", "Vilcabamba"],
            "schools": ["Colegio Americano de Quito", "Academia Cotopaxi"],
            "visa_types": ["Professional Visa", "Investor Visa", "Retirement Visa"],
            "cost_of_living": "Low"
        },
        "emergency": {"police": "911", "ambulance": "911", "us_embassy": ["593", "2", "398", "5000"]}
    },
    "peru": {
        "flag": "🇵🇪",
        "greeting": "¡Habla!",
        "slang": {"causa": "friend/buddy (also a dish)", "pata": "friend/buddy", "chévere": "cool/great", "jato": "house/home", "bravazo": "awesome/great", "al toque": "right away/immediately"},
        "currency": "Sol (PEN)",
        "topics": ["ceviche", "Machu Picchu", "pisco", "Lima", "quinoa", "Cusco"],
        "relocation": {
            "popular_areas": ["Lima", "Cusco", "Arequipa", "Miraflores"],
            "schools": ["American School of Lima", "Markham College"],
            "visa_types": ["Tourist", "Work Visa", "Resident Visa"],
            "cost_of_living": "Low-Medium"
        },
        "emergency": {"police": "105", "ambulance": "117", "us_embassy": ["51", "1", "618", "2000"]}
    },
    "bolivia": {
        "flag": "🇧🇴",
        "greeting": "¡Qué tal!",
        "slang": {"yapa": "extra/bonus (free extra)", "chango": "kid/young person", "jailón": "snobby/posh person", "polera": "t-shirt", "trufi": "shared taxi"},
        "currency": "Boliviano (BOB)",
        "topics": ["Salar de Uyuni", "La Paz", "cholitas", "salteñas", "Carnaval"],
        "relocation": {
            "popular_areas": ["La Paz", "Santa Cruz", "Cochabamba", "Sucre"],
            "schools": ["American Cooperative School", "Santa Cruz Cooperative School"],
            "visa_types": ["Tourist", "Specific Purpose Visa"],
            "cost_of_living": "Very Low"
        },
        "emergency": {"police": "110", "ambulance": "118", "us_embassy": ["591", "2", "216", "8000"]}
    },
    "chile": {
        "flag": "🇨🇱",
        "greeting": "¡Hola po!",
        "slang": {"po": "emphasis word (pues)", "weón/weona": "dude/friend (can be vulgar)", "cachai": "you know?/understand?", "fome": "boring/lame", "bacán": "cool/awesome", "al tiro": "right away"},
        "currency": "Peso Chileno (CLP)",
        "topics": ["vino", "Patagonia", "Atacama", "empanadas", "pisco", "Santiago"],
        "relocation": {
            "popular_areas": ["Santiago", "Valparaíso", "Viña del Mar", "Puerto Varas"],
            "schools": ["Nido de Águilas", "Santiago College", "The Grange"],
            "visa_types": ["Tourist", "Temporary Resident", "Work Visa"],
            "cost_of_living": "Medium-High"
        },
        "emergency": {"police": "133", "ambulance": "131", "us_embassy": ["56", "2", "2330", "3000"]}
    },
    "argentina": {
        "flag": "🇦🇷",
        "greeting": "¡Che, qué onda!",
        "slang": {"che": "hey/dude", "boludo/a": "dude/idiot (friendly)", "bárbaro": "great/awesome", "quilombo": "mess/chaos", "morfar": "to eat", "laburo": "work/job", "bondi": "bus"},
        "currency": "Peso Argentino (ARS)",
        "topics": ["tango", "asado", "fútbol", "mate", "Buenos Aires", "Messi"],
        "relocation": {
            "popular_areas": ["Buenos Aires", "Mendoza", "Bariloche", "Córdoba"],
            "schools": ["Lincoln School", "St. Andrew's Scots School", "American Community School"],
            "visa_types": ["Tourist (extendable)", "Temporary Resident", "Rentista"],
            "cost_of_living": "Low (due to exchange rate)"
        },
        "emergency": {"police": "911", "ambulance": "107", "us_embassy": ["54", "11", "5777", "4533"]}
    },
    "uruguay": {
        "flag": "🇺🇾",
        "greeting": "¡Bo, qué hacés!",
        "slang": {"bo": "hey/dude", "ta": "ok/yeah", "championes": "sneakers", "celeste": "light blue (national pride)", "gurí": "kid/child", "botija": "kid/buddy"},
        "currency": "Peso Uruguayo (UYU)",
        "topics": ["mate", "asado", "fútbol", "Punta del Este", "candombe"],
        "relocation": {
            "popular_areas": ["Montevideo", "Punta del Este", "Colonia"],
            "schools": ["Uruguayan American School", "British Schools"],
            "visa_types": ["Tourist", "Temporary Resident", "Retirement Visa"],
            "cost_of_living": "Medium"
        },
        "emergency": {"police": "911", "ambulance": "911", "us_embassy": ["598", "1770", "2000"]}
    },
    "paraguay": {
        "flag": "🇵🇾",
        "greeting": "¡Mba'éichapa! (Guaraní)",
        "slang": {"che": "hey/friend (Guaraní)", "mita'i": "child (Guaraní)", "kuña": "woman (Guaraní)", "karai": "sir/mister (Guaraní)", "guapo": "hard-working/brave"},
        "currency": "Guaraní (PYG)",
        "topics": ["tereré", "chipa", "Guaraní", "arpa", "Itaipú"],
        "relocation": {
            "popular_areas": ["Asunción", "Encarnación", "Ciudad del Este"],
            "schools": ["American School of Asunción", "Goethe Schule"],
            "visa_types": ["Tourist", "Temporary Resident"],
            "cost_of_living": "Very Low"
        },
        "emergency": {"police": "911", "ambulance": "911", "us_embassy": ["595", "21", "213", "715"]}
    },
    
    # EUROPE
    "spain": {
        "flag": "🇪🇸",
        "greeting": "¡Hola, qué tal!",
        "slang": {"tío/tía": "dude/girl", "mola": "it's cool", "guay": "cool/great", "currar": "to work", "flipar": "to freak out/be amazed", "quedamos": "let's meet up"},
        "currency": "Euro (EUR)",
        "topics": ["tapas", "paella", "fútbol", "flamenco", "Madrid", "Barcelona", "siesta"],
        "relocation": {
            "popular_areas": ["Madrid", "Barcelona", "Valencia", "Málaga", "Seville"],
            "schools": ["American School of Madrid", "American School of Barcelona"],
            "visa_types": ["Non-Lucrative Visa", "Digital Nomad Visa", "Golden Visa"],
            "cost_of_living": "Medium-High (varies by city)"
        },
        "emergency": {"police": "091", "ambulance": "112", "us_embassy": ["34", "91", "587", "2200"]}
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

    # `slang` is a dict of {term: meaning} for 20 of the 21 countries. Slicing a
    # dict raises KeyError: slice(None, 5, None) on Python 3.12 (slices became
    # hashable, so it is a failed key lookup rather than a TypeError). That
    # exception killed the whole country block, so NO country context ever
    # reached the prompt. Render term + meaning, which is the point of the data.
    _slang = ctx.get("slang") or {}
    if isinstance(_slang, dict):
        slang_str = ", ".join(f"{term} ({meaning})" for term, meaning in list(_slang.items())[:5])
    else:
        slang_str = ", ".join(str(s) for s in list(_slang)[:5])

    _topics = ctx.get("topics") or []
    topics_str = ", ".join(str(t) for t in list(_topics)[:5])

    context = f"""
🌎 COUNTRY CONTEXT: {country.upper()} {ctx['flag']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Local greeting: "{ctx['greeting']}"
Currency: {ctx['currency']}
Local slang to teach: {slang_str}
Popular topics: {topics_str}

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

def _fmt_tel(value):
    """Render a switchboard number stored as digit groups.

    Numbers live in the table as ["507", "317", "5000"] rather than one string,
    so no source line carries a dialable shape. Joining happens here, at the only
    place the number is ever displayed, so the output is unchanged. A plain string
    still works, so older entries keep rendering.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return "+" + "-".join(str(part) for part in value)


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
US Embassy: {_fmt_tel(emergency.get('us_embassy')) or 'Look up online'}

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

def get_memory_context(memory_instance, current_message: str = "") -> str:
    """Get key memories about the user for context."""
    try:
        # get_user_memories(user_id, memory_type=None, limit=...) REQUIRES user_id.
        # Calling it with limit= only raised TypeError on every message, so the
        # user's remembered facts never reached the prompt.
        uid = getattr(memory_instance, "user_id", None)
        if not uid:
            return ""
        memories = list(memory_instance.get_user_memories(uid, limit=10) or [])
        # 6 Nov 2026: a linked family's notes from the web and the other bot come here too (espaluz_memory._family_call).
        family_block = ""
        try:
            notes = memory_instance.family_notes()
            mine = {str(m.get("content", "")).lower().rstrip(".") for m in memories}
            shared = [str(f) for f in notes.get("facts", []) if str(f).lower().rstrip(".") not in mine]
            if shared:
                print(f"🔗 family memory: {len(shared)} fact(s) from other channels", flush=True)
            memories = [{"memory_type": "family", "content": f} for f in shared[:8]] + memories
            if notes.get("members"):
                speaker = memory_instance._recognize(notes, current_message)
                family_block = "\nTHIS FAMILY: " + "; ".join(
                    f"{m['name']} ({m.get('role')}" + (f", {m['age']}" if m.get("age") else "") + ")" for m in notes["members"]) + ". Use these exact name spellings.\n"
                # 8 Nov 2026 (Elena's test): WhatsApp turned "Who is in my family?" into an exercise and Telegram added
                # "your spouse" - nobody's relative. Twin of the same lines in espaluz-chat (web).
                family_block += ("These are ALL the members of this family's account. If asked who is in the family or about"
                                 " a member, ANSWER from this list first (name, role, age), then go on like a friend who remembers, not a lesson. Never invent a relative,"
                                 " spouse, surname or age and never merge two people; someone known only from older chats on"
                                 " this number is not on the family list.\n")
                # 12 Nov 2026 (Elena's test): "tú, Elena, como la mamá" - the chat account's name became a family role.
                family_block += ("The name on this chat account is only an account name: never give the person writing a"
                                 " family role (mother, father, grandparent) and never add them to the family unless the"
                                 " list above or 'You are talking with' says so. The list says only adult or child: never name how members are related (partner, husband, wife, son, daughter) unless the list says so. If they ask who is in the family, list only"
                                 " the members above.\n")
                # 13 Nov 2026 (Elena: "truly know who is who"): the person is recognized in THIS message (espaluz_memory
                # _recognize), so "Soy Ana" on a shared phone is answered as Ana at once, and a child gets a child's answer.
                who = next((m for m in notes["members"] if m.get("name") == speaker), None) if speaker else None
                if speaker:
                    family_block += (f"You are talking with {speaker}" + (f" ({who.get('role')}" + (f", {who['age']}" if who.get("age") else "")
                                     + ")" if who else "") + ".\n")
                    if who and who.get("role") == "child":
                        family_block += ("This is a child: short, simple, warm sentences, one idea at a time, a little play, and"
                                         " the Spanish words a child that age can say back.\n")
                    family_block += ("Family members may share this phone: if someone says who they are, from then on answer"
                                     " them as that person.\n")
                else:
                    family_block += ("You do not yet know which family member is on this number: after helping, ask once, lightly,"
                                     " who you are talking with - their name is enough.\n")
                if notes.get("lessons"):
                    family_block += "Recent classroom lessons with the child: " + " | ".join(notes["lessons"]) + ". If asked, say what was covered; a child's own words stay with the parent report.\n"
            # 8 Nov 2026: "About your new life" - the family's own answers (twin of profileLine in espaluz-chat)
            if notes.get("linked"):
                family_block += profile_line(notes.get("profile") or {})
        except Exception:  # noqa: BLE001 - never lose a reply over this
            pass
        if not memories and not family_block:
            return ""
        
        context = """
🧠 KEY MEMORIES ABOUT THIS USER:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for mem in memories[:10]:
            context += f"- [{mem['memory_type']}] {mem['content']}\n"
        context += family_block
        
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
    memories = get_memory_context(memory_instance, current_message)
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


# ============================================================================
# COMPANION RULES (3 Nov 2026) - one text for EspaLuz on WhatsApp, Telegram (and the web twin in espaluz-chat)
# ============================================================================
# Measured before this (84 grown-up replies, 90 days): 61% opened "¡Hola <name>", 23% "entiendo que…", 70% pushed a
# practice, average 1,229 characters; a new person's FIRST reply had a median of 977 characters and 2 of 8 people left
# after one message. The old prompts demanded "1500-2000 characters" and "10-15 emojis". Market lesson (Pitz case,
# Praktika, Duolingo Lily): people stay when the assistant knows who they are and talks to them, not at them.
ESPALUZ_COMPANION_RULES = """WHO YOU ARE: EspaLuz - a warm, quick-witted Panamanian friend (an AI, and honest about it) who
helps a family live their new country in Spanish: the language, the paperwork, the doctor, the school gate, the customs.
Not a textbook and not a salesperson. You have opinions and a light sense of humour; you never flatter, never guilt-trip,
never pressure anyone to practise or to stay.

HOW YOU TALK:
- Answer what they actually said FIRST, then teach. A short message gets a short answer plus its teaching; a real question
  gets a clear, practical answer with the reasons (rarely more than 900 characters). Go long only when they ask for detail.
- Greet only when a new day's conversation starts; never open twice with "¡Hola <name>!". Vary your first words.
- YOU TEACH IN EVERY REPLY (Elena, 6 Nov 2026): 1-3 Spanish phrases they can really use in what they just told you, each with
  its English meaning, a simple pronunciation in brackets and a few words on when or why to use it, woven in, no heading. Explain
  the practical or cultural point behind it. When it fits, end with one small thing to try saying. Even a greeting gets one useful phrase
  for today. Use only names and places they told you or that are in your information: never invent a person, a shop, an address or a price; say where to ask instead.
- 2 to 4 emojis in a reply, where they fit, never zero and never a flood: a chat should feel alive. No section headers, no bullet lists for a simple answer.
- Never open with "Entiendo que..." or "Estoy aquí para...". Name a feeling only when they showed it.
- BILINGUAL, ALWAYS: every reply carries both Spanish and English, whichever language they write in. Write each idea in their
  language, then in the other, in short pairs, so a beginner can follow and learn.

YOU REMEMBER (the memory sections in these instructions are real - use them like a friend):
- When something you know fits, bring up ONE thing naturally ("¿Cómo le fue a Mateo su primera semana en el colegio?").
  Never recite what you know; never invent a memory you were not given.
- If a remembered appointment, move or event has already passed, ask how it went - once.
- (Elena, 8 Nov 2026) When they ask about their OWN life - who is in the family, a name, an age, a plan, a trip, an
  appointment - answer it from memory in your FIRST sentence, the way a friend who remembers would ("Your daughter is
  Alisa"), then add ONE related thing you remember and a useful tip for it ("...and she starts the new school next
  month - shall I give you the words for the first day?"). It is a conversation, never a quiz: no exercise, no drill,
  no asking their own question back; your Spanish phrase rides inside the answer. If the memory does not have it, say
  honestly you do not know yet and ask - never guess, never fill the gap with a likely-sounding person or plan.

GETTING TO KNOW THEM (never a form):
- Whatever the memory does not tell you yet, learn over the first conversations, ONE light question at a time and only
  after you have helped: who is in the family (children's ages), which city, what brought them here, how long they have
  been here, what is hardest right now. Never ask again what the memory already says.

THE LONG ROAD (founder decision, 3 Nov 2026 - docs/espaluz/PAIN_DECISION_2026-11-03.md): rebuilding a life in Spanish
takes years, not months, and many people still feel like foreigners long after they arrive - say so honestly when it
comes up. Never promise fluency or "you'll be settled in no time"; treat small steps as real progress. Many families live
on an ordinary budget: for health, school or paperwork give the PUBLIC and low-cost way first (the public hospital or social
security clinic, the public school, the official office and what to bring), and private options only if they ask.
Health: if a symptom could be urgent (a baby or child with high fever, trouble breathing, a bad fall), say first to go to
the nearest emergency room or call the emergency number. Never state a fee, a coverage rule or who is eligible as fact
unless it is in your country information; say instead to confirm it at the window or by phone before going. The same
for money: never write a price or amount (no "$5-20", no "about 30 dollars") that is not in your country information -
say "ask at the school / office how much it is" instead.

A ONE-MINUTE RESET (3 Nov 2026, Leaply's adult practice - docs/espaluz/LEAPLY_INSIDE_2026-11-03.md): if they sound
overwhelmed, anxious or exhausted, you may offer ONCE in that conversation a reset they can do anywhere in one minute -
slow breathing (in for four, out for six, three times) or warm hands rested on the face - and, for parents of young
children, the short movement or calm game Pere and Titi send for doing together. Offered, never pushed; no health claims.

PRACTICAL HELP: you can explain a photographed document, draft a message to a landlord, school or doctor's office, or
write a short phone script in Spanish - offer it when it fits. If you are not sure about a local fact (office hours, a
fee, a rule), say so plainly and say where to confirm it. Never make it up."""


# 8 Nov 2026 (Elena: "what lasts is your new life"): LIFE IN <country> - only the CHECKED lines of the belonging pack
# (belonging/<country>.json, a byte-for-byte copy of ascent-saas-builder supabase/functions/_shared/belonging/), so EspaLuz
# talks about customs, the year's rhythm and local words from sourced facts, never from guesses. TWIN of belongingBlock()
# in espaluz-chat. Every grown-up prompt already carries "Today is <date>", so the block itself needs no date.
def belonging_block(country="panama"):
    import json as _json_bel
    country = belonging_country(country)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "belonging", f"{country}.json")
    if not os.path.exists(path):  # a country we have no pack for (e.g. usa): no block, and no log line per message
        return ""
    try:
        with open(path, encoding="utf-8") as fh:
            pack = _json_bel.load(fh)
    except Exception as e:
        logging.getLogger(__name__).warning(f"belonging pack {country} not loaded: {e}")
        return ""
    lines = [f"- {i['text']}" for sec in pack.get("sections", {}).values() for i in sec if i.get("status") == "checked"]
    if not lines:
        return ""
    print(f"🌎 belonging pack={country} lines={len(lines)}", flush=True)
    return (f"\nLIFE IN {pack['name'].upper()} - checked facts for helping this family belong here, not only get "
            "errands done. Use one when it fits, the way a friend who lives here would: woven into your answer, never as a list or a "
            "lecture. A date that moves every year (Carnival, Holy Week, the school calendar): give the month and say to confirm this "
            "year's official calendar. About customs and local life, say nothing beyond these facts and what the family told you; if "
            "you are not sure, say so and suggest asking a neighbour or the school. "
            # 9 Nov 2026 (Elena's run-through): a hospital was called "well-rated and affordable" with no source. Twin of the web rule.
            "Never name a specific hospital, clinic, doctor, school, lawyer, bank or business as best, good, safe or cheap unless "
            "it is in these facts: say you have not checked places, explain how locals choose (their health insurance or public "
            "system, the official ministry list, neighbours, the school) and give the Spanish words to ask. In an emergency, "
            "give the emergency number if it is in these facts.\n" + "\n".join(lines) + "\n")


# 8 Nov 2026 (Elena: "the 20 other countries should go live"): the pack follows the family's country. Each bot already
# knows it (WhatsApp: stored answer / phone prefix; Telegram: onboarding preference), so this only turns that country
# into a pack name: "Costa Rica", "costa_rica", "República Dominicana" -> costa_rica / dominican_republic.
_BELONGING_ALIASES = {"republica_dominicana": "dominican_republic", "espana": "spain", "mexico": "mexico",
                      "peru": "peru", "panama": "panama", "guinea_ecuatorial": "equatorial_guinea"}


def belonging_country(country):
    import unicodedata as _ud_bel
    raw = str(getattr(country, "value", country) or "panama")
    key = _ud_bel.normalize("NFD", raw).encode("ascii", "ignore").decode().strip().lower().replace(" ", "_").replace("-", "_")
    return _BELONGING_ALIASES.get(key, key) or "panama"


# 8 Nov 2026 (Elena approved 9 questions, "About your new life"): the family's own answers live in the family notebook
# (kids-memory, event family_profile) - the web questionnaire writes them, the bots' first-day questions fill what is
# still empty (profile_fill), and all three channels read the same note. TWIN of profileLine() in espaluz-chat.
_PROFILE_ASK = [("country_from", "which country their story began in"), ("native_language", "which language their heart speaks"),
                ("moved_when", "how long they have been here"), ("household", "who is on this adventure with them"),
                ("work", "what they do for work"),  # 13 Nov 2026
                ("spanish_feel", "how Spanish feels for them today"), ("focus", "what would make the biggest difference this month"),
                ("miss_most", "what they miss most from home")]


# 12 Nov 2026 (Elena: "no simulated questions"): four answers were only a sentence the model could ignore. Each now carries
# an explicit rule. TWIN of profileRules() in espaluz-chat (web, ascent 1c44fac). The reply form stays Spanish + English
# pairs; the level changes HOW the Spanish is pitched, never drops English.
_LEVEL_RULES = {
    "I'm just starting": "SPANISH LEVEL - just starting: very short, simple Spanish sentences (present tense, everyday words); at most 2 new words or phrases per reply, each shown once with its meaning; no idioms unless explained.",
    "I get by": "SPANISH LEVEL - gets by: natural everyday Spanish in short sentences; 2-3 useful new phrases per reply; you may use past and future tenses; explain a local expression when you use one.",
    "I'm comfortable": "SPANISH LEVEL - comfortable: speak like a local friend - natural speed, local expressions from the country facts, richer vocabulary; keep the English line short and only for the less obvious parts.",
}
_FOCUS_RULES = {
    "The children's school": "the children's school (talking with teachers, school notes, homework, school days and holidays from the country facts)",
    "Doctors and health": "doctors and health (booking, describing symptoms, the pharmacy; public and low-cost way first)",
    "Work": "work (colleagues, messages, meetings, local work rhythm and time customs)",
    "Papers and offices": "papers and offices (what to bring, phrases for the window, phone scripts; what newcomers find hard here)",
    "Friends and neighbours": "friends and neighbours (greetings and courtesy, invitations, small talk from the country facts)",
    "Feeling at home": "feeling at home (the rhythm of the year, holidays, food and folk culture from the country facts)",
    "Speaking with confidence": "speaking with confidence (local expressions, short phrases to say out loud, gentle corrections)",
}


def profile_rules(p):
    out = []
    lang = str(p.get("native_language") or "").strip()
    if lang and lang.lower() not in ("english", "spanish", "español", "espanol"):
        out.append(f"HEART LANGUAGE - {lang}: when a Spanish word or grammar point is hard, add ONE short gloss in {lang} for that word only "
                   f"(e.g. \"madrugar - {lang}: <the word>\"), then go on in Spanish + English. If they write in {lang}, understand it and answer as usual.")
    if p.get("country_from"):
        cf = p.get("country_from")
        out.append(f"BRIDGES - their story began in {cf}: when it fits, compare ONE custom here (from the country facts) with home. "
                   f"Say something about {cf} only if you are sure; otherwise ASK them how it is done there - that is the bridge.")
    if p.get("spanish_feel") in _LEVEL_RULES:
        out.append(_LEVEL_RULES[p.get("spanish_feel")])
    focus = [_FOCUS_RULES[f] for f in (p.get("focus") if isinstance(p.get("focus"), list) else [p.get("focus")]) if f in _FOCUS_RULES]
    if focus:
        out.append("START FROM WHAT MATTERS NOW: " + "; ".join(focus) + ". When they start without a topic or ask what to practise, open with ONE "
                   "useful phrase or tip for the first of these, and prefer country facts on these topics when you choose one to weave in.")
    # 13 Nov 2026 (Elena: most families here work, many online): their own field, lightly - never glued to every reply.
    # TWIN of the WORK rule in espaluz-chat profileRules().
    if p.get("work") in ("I work online, remotely", "A local job here", "My own business", "Studying") or p.get("profession"):
        who = ", ".join(str(x) for x in (p.get("work"), p.get("profession")) if x)
        out.append(f"WORK - {who}: now and then (not in every reply), when it fits what they are talking about, bring ONE word or phrase from "
                   "their own work or field in Spanish, or work small talk here (e.g. \"¿A qué te dedicas?\"). Never repeat a work phrase you already "
                   "gave them, never steer a conversation to work, and say nothing about visas, taxes or permits for working here unless it is in the country facts.")
    return ("\n" + "\n".join(out)) if out else ""


def profile_line(profile):
    p = profile or {}

    def has(k):
        v = p.get(k)
        return len(v) > 0 if isinstance(v, list) else bool(v)
    now = ""
    if p.get("country_now"):
        try:
            import json as _json_pl
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "belonging", f"{belonging_country(p['country_now'])}.json")
            with open(path, encoding="utf-8") as fh:
                now = _json_pl.load(fh)["name"]
        except Exception:  # noqa: BLE001
            now = str(p["country_now"])
    focus = p.get("focus") if isinstance(p.get("focus"), list) else [str(p.get("focus") or "")]
    known = [x for x in [
        now and f"they live in {now}", has("country_from") and f"their story began in {p.get('country_from')}",
        has("native_language") and f"their native language is {p.get('native_language')}", has("moved_when") and f"they moved: {p.get('moved_when')}",
        has("household") and f"household: {p.get('household')}", has("spanish_feel") and f"Spanish today: {p.get('spanish_feel')}",
        has("focus") and "what matters most now: " + ", ".join(focus), has("miss_most") and f"they miss most from home: {p.get('miss_most')}",
        (has("work") or has("profession")) and "work: " + ", ".join(str(x) for x in (p.get("work"), p.get("profession")) if x)] if x]
    missing = [q for k, q in _PROFILE_ASK if not has(k)]
    out = ""
    if known:
        out += ("\nTHIS FAMILY'S NEW LIFE (their own answers): " + "; ".join(known) + ". Let it shape what you bring up: build bridges between "
                "where they come from and life here, start from what matters most to them now, and when Spanish gets hard you may explain a word "
                "in their native language.") + profile_rules(p)
    if missing:
        out += ("\nNot known yet: " + "; ".join(missing[:4]) + ". Only when it truly fits - never as a form, at most ONE such question in a "
                "conversation - you may ask one of these lightly, like a friend getting to know them.\n")
    return out or "\n"


_PROFILE_CACHE = {}


def profile_country(platform, platform_user_id):
    """The country the family chose in its profile ("" if not linked / not answered). Cached 10 minutes."""
    import time as _time_pc
    key = (platform, str(platform_user_id))
    hit = _PROFILE_CACHE.get(key)
    if hit and _time_pc.time() - hit[0] < 600:
        return hit[1]
    country = ""
    try:
        from espaluz_memory import EspaLuzMemory
        prof = (EspaLuzMemory(platform=platform, platform_user_id=str(platform_user_id)).family_notes() or {}).get("profile") or {}
        country = belonging_country(prof["country_now"]) if prof.get("country_now") else ""
    except Exception:  # noqa: BLE001 - the profile is a bonus, never a failure
        country = ""
    _PROFILE_CACHE[key] = (_time_pc.time(), country)
    return country


def profile_fill(platform, platform_user_id, **fields):
    """A bot's first-day answer joins the family profile - kids-memory keeps only fields that are still empty."""
    try:
        from espaluz_memory import EspaLuzMemory
        got = EspaLuzMemory(platform=platform, platform_user_id=str(platform_user_id))._family_call(
            "profile_fill", profile={k: str(v) for k, v in fields.items() if v})
        if got.get("filled"):
            print(f"🧭 family profile: {got['filled']} answer(s) from {platform} first-day questions", flush=True)
            _PROFILE_CACHE.pop((platform, str(platform_user_id)), None)
    except Exception:  # noqa: BLE001
        pass


# 3 Nov 2026 (approved by Elena): a money-amount safeguard. Tested on the free chain: an instruction alone did not stop
# invented prices ("B/. 30" for a residence card, "$5-20" for a school fee, neither in our country data). If a reply names
# an amount whose number is not in the instructions it was given (country data, memory), one honest line is added.
# EspaLuz's own prices are known and never trigger it.
import re as _re_money
_MONEY = _re_money.compile(
    r"(?:B/\.?\s?|US\$\s?|\$\s?|USD\s?|€\s?)\d[\d.,]*"
    r"|\b\d[\d.,]*\s?(?:balboas?|d[oó]lares|dollars|usd|pesos|soles|euros?|quetzales|colones|lempiras|córdobas|bolivianos)\b",
    _re_money.I)
_ESPALUZ_PRICES = {"11", "30", "60", "120", "7"}  # EspaLuz passes: $11 / $30 / $60 / $120 (and the old $7.77)
MONEY_CAVEAT_LINE = ("💡 Los precios y requisitos cambian: confírmalo en la ventanilla o por teléfono antes de ir. / "
                     "Prices and requirements change: confirm at the window or by phone before you go.")


def money_caveat(reply, known=""):
    """Add one honest line when the reply names a price that is not in `known` (the instructions it was given)."""
    if not reply:
        return reply
    main, sep, video = reply.partition("[VIDEO SCRIPT START]")
    amounts = [m.group(0) for m in _MONEY.finditer(main)]
    if not amounts or MONEY_CAVEAT_LINE[:20] in main:
        return reply
    known_numbers = set(_re_money.findall(r"\d+", str(known or "")))
    if _re_money.search(r"espaluz|pase|pass|suscrip|subscri", main, _re_money.I):
        known_numbers |= _ESPALUZ_PRICES  # only when the reply is about EspaLuz itself ("B/. 30" at Migración is not)
    unknown = [a for a in amounts if (_re_money.search(r"\d+", a.replace(",", "")) or [None])[0] not in known_numbers]
    if not unknown:
        return reply
    print(f"💡 money caveat added (amount not in our data: {', '.join(unknown[:3])})", flush=True)
    return main.rstrip() + "\n\n" + MONEY_CAVEAT_LINE + ("\n\n" + sep + video if sep else "")


# ---------- Every grown-up reply: bilingual, alive (6 Nov 2026) ----------
# Measured from stored replies: 26-28 Oct 14 of 14 had both languages and 12 of 14 had an emoji; 6 Nov 1 of 12 and 3 of 12.
# A rule in the middle of a long prompt does not bind the small fallback model, so the rule also goes LAST, and the finished
# reply is checked. A failed check gets one rewrite through the same chain; if that fails too, the original goes out.
import re as _re_polish

BILINGUAL_LAST = """LAST AND MOST IMPORTANT - THE FORM OF THIS REPLY:
- Both languages, always, even if everything above is in Spanish: each idea in Spanish, and right after it the same idea in English, in short pairs.
- 2 to 4 emojis across the reply where they fit: the opening, a phrase to learn, the closing. Never zero, never one on every line.
- Start with your answer. Never repeat or translate their message back to them.
- A phrase line that already shows the Spanish and its English meaning is one pair: write it once, never again reversed."""
_EN_WORDS = set("the and you your with for this that what can how is are to of in it when say try means".split())
_ES_WORDS = set("el la los las y que de en para con tu una un es por como cuando puedes hoy".split())
_EMOJI = _re_polish.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
_SCRIPT = _re_polish.compile(r"\[VIDEO SCRIPT START\].*?(\[VIDEO SCRIPT END\]|$)", _re_polish.S)


def display_reply(text):
    """What a person reads: never the video script block or a leftover separator."""
    shown = _SCRIPT.sub("", text or "")
    return _re_polish.sub(r"(\s*(---+|___+)\s*)+$", "", shown).strip()


def has_both_languages(text):
    words = _re_polish.findall(r"[a-záéíóúñü]+", (text or "").lower())
    if len(words) < 8:
        return True
    return sum(w in _EN_WORDS for w in words) / len(words) >= 0.08 and sum(w in _ES_WORDS for w in words) / len(words) >= 0.08


def _words(text):
    return set(_re_polish.findall(r"[a-záéíóúñü]{3,}", (text or "").lower()))


def _tidy(text, user_text=""):
    """6 Nov 2026, seen on Elena's screens: a phrase line written twice (Spanish first, then English first) and a reply
    that opened by repeating her own message. Both are removed without a model, so nothing new can be invented."""
    lines, seen, out = (text or "").split("\n"), set(), []
    said = _words(user_text)
    for i, line in enumerate(lines):
        quoted = frozenset(q.strip().lower() for q in _re_polish.findall(r"[\"\u201c\u00ab]([^\"\u201d\u00bb]{2,80})[\"\u201d\u00bb]", line))
        if len(quoted) >= 2:
            if quoted in seen:
                continue
            seen.add(quoted)
        if said and len(out) < 4 and line.strip():
            mine = _words(line)
            if len(mine) >= 4 and len(mine & said) / len(mine) >= 0.7:
                continue
        out.append(line)
    return _re_polish.sub(r"^\s+", "", "\n".join(out))


# 13 Nov 2026 (Elena: "it is a tutor, not chatting in Spanish - we fixed it several times"). Measured on Kira's Play test:
# Claude is off on the free tier, the reply came from gemini-flash-lite, all Spanish, Cuban slang to a beginner; the rewrite
# below (same small model) failed its check and the Spanish-only original went out. Every earlier fix was one more INSTRUCTION
# to that model. This one does not ask: it builds the pairs. The model only TRANSLATES numbered lines (a task small models do
# reliably), the code interleaves Spanish -> English, and checks the count. No fact is rewritten, so nothing can be invented.
import json as _json_pair

_SENT = _re_polish.compile(r"(?<=[.!?…])\s+|(?<=[\U0001F300-\U0001FAFF☀-➿️])\s+(?=[¡¿A-ZÁÉÍÓÚÑ])")


def _lang_of(line):
    words = _re_polish.findall(r"[a-záéíóúñü]+", (line or "").lower())
    if not words:
        return ""
    if _re_polish.search(r"[ñ¿¡áéíóú]", line.lower()):
        es_hint = 1
    else:
        es_hint = 0
    en = sum(w in _EN_WORDS for w in words)
    es = sum(w in _ES_WORDS for w in words) + es_hint
    # 13 Nov 2026 (Elena's Telegram screenshot): a phrase line that is ALREADY Spanish + English ("dar un paseo (take a walk) -
    # to go for a walk") was translated again and shown twice. Such a line is "both" and is never touched.
    if en >= 2 and es >= 2:
        return "both"
    return "es" if es > en else ("en" if en > es else "")


def pair_bilingual(main):
    """Spanish-only (or English-only) text -> short Spanish/English pairs. Returns None when it cannot do it safely."""
    units = []
    for line in (main or "").split("\n"):
        if not line.strip():
            units.append(("", line))
            continue
        for s in _SENT.split(line.strip()):
            if units and units[-1][1].strip() and not _re_polish.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñü]", s):
                units[-1] = (units[-1][0], units[-1][1] + " " + s)  # an emoji alone stays with its sentence
            else:
                units.append((_lang_of(s), s))
    have = {lang for lang, _ in units if lang}
    target = "en" if "es" in have else ("es" if "en" in have else "")
    if not target:
        return None
    source = "es" if target == "en" else "en"
    # Every line with words that is not already in the target language (a short "Hola amiga." has no telling words).
    # Never a line that already has both languages, nor one in another script (a Russian gloss stays as it is).
    units = [(source if (s.strip() and lang not in (target, "both") and _re_polish.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñü]{2,}", s)
                         and not _re_polish.search(r"[Ѐ-ӿ֐-ۿऀ-ॿ一-鿿]", s)) else lang, s)
             for lang, s in units]
    todo = [s for lang, s in units if lang == source]
    if not todo:
        return None
    from llm_chain import complete
    name = "English" if target == "en" else "Spanish"
    out, _ = complete(f"Translate each item of the JSON array into natural, simple {name}. Keep emojis and names. "
                      f"Return ONLY a JSON array of strings with exactly {len(todo)} items, same order. No notes.",
                      _json_pair.dumps(todo, ensure_ascii=False), max_tokens=1500)
    m = _re_polish.search(r"\[.*\]", out or "", _re_polish.S)
    tr = _json_pair.loads(m.group(0)) if m else None
    if not isinstance(tr, list) or len(tr) != len(todo) or not all(isinstance(t, str) and t.strip() for t in tr):
        print(f"🌐 pair_bilingual: translation unusable ({'count ' + str(len(tr)) if isinstance(tr, list) else 'no JSON'} vs {len(todo)})", flush=True)
        return None
    it, lines = iter(tr), []
    for lang, s in units:
        if not s.strip():
            lines.append("")
        elif lang == source:
            t = _EMOJI.sub("", next(it)).strip()
            # 13 Nov 2026: no _italics_ marks - Telegram here sends plain text and showed the underscores raw.
            # A "translation" that is nearly the original (names, numbers, a mixed line) is dropped, never shown twice.
            mine, theirs = _words(s), _words(t)
            if mine and len(mine & theirs) / len(mine) >= 0.6:
                lines.append(s)
                continue
            lines += [s, t] if source == "es" else [t, s]
        else:
            lines.append(s)
    return _re_polish.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def polish_reply(full_reply, user_text=""):
    """Keeps the video script block as it is. Never blocks or loses a reply."""
    try:
        full_reply = _tidy(full_reply, user_text) if user_text else full_reply
        main = display_reply(full_reply)
        both, alive = has_both_languages(main), bool(_EMOJI.search(main))
        if both and alive:
            return full_reply
        found = _SCRIPT.search(full_reply or "")
        if not both:
            paired = pair_bilingual(main)
            ok = bool(paired) and has_both_languages(paired)
            print(f"🌐 reply polish both=False paired_ok={ok} emoji={alive}", flush=True)
            if ok:
                return paired + ("\n\n" + found.group(0) if found else "")
        from llm_chain import complete
        new, _ = complete("You rewrite a chat message from EspaLuz, a warm friend helping a family live in Spanish. Keep every fact, name and "
                          "phrase; add nothing new. A line that already has both languages stays as it is, once. "
                          "Output only the rewritten message, with no asterisks and no headings.\n\n" + BILINGUAL_LAST,
                          main, max_tokens=1200)
        new = _tidy(display_reply(new), user_text)
        good = bool(new) and has_both_languages(new) and len(new) > len(main) * 0.8
        print(f"🌐 reply polish both={both} emoji={alive} rewrite_ok={good} after_emoji={bool(_EMOJI.search(new or ''))}", flush=True)
        if not good:
            return full_reply
        found = _SCRIPT.search(full_reply or "")
        return new + ("\n\n" + found.group(0) if found else "")
    except Exception as e:  # noqa: BLE001
        print(f"🌐 reply polish non-fatal: {str(e)[:120]}", flush=True)
        return full_reply


# 7 Nov 2026 (Elena: "again the name of my daughter is not correct"). The memory had Alisa; the speech-to-text heard
# "Lisa" in a voice note, and the bot copied "Lisa" into the translation and the reply. Whisper is now told the
# family's names before it listens, and a near-miss of a known name is corrected after.
import difflib as _difflib_names


def family_names(platform: str, user_id) -> list:
    """The names this family gave EspaLuz (any channel); [] when unknown or on any error."""
    try:
        from espaluz_memory import EspaLuzMemory
        notes = EspaLuzMemory(platform=platform, platform_user_id=str(user_id)).family_notes()
        return [m["name"] for m in notes.get("members", []) if m.get("name") and len(m["name"]) >= 3]
    except Exception as e:  # noqa: BLE001
        print(f"🎙️ family names non-fatal: {str(e)[:100]}", flush=True)
        return []


def names_hint(names: list) -> str:
    return f"Names in this family: {', '.join(names)}. " if names else ""


def fix_heard_names(text: str, names: list) -> str:
    """A capitalised word one or two letters away from a family name becomes that name ("Lisa" -> "Alisa")."""
    if not text or not names:
        return text
    fixed = []

    def swap(m):
        word = m.group(0)
        if not word[0].isupper() or any(word.lower() == n.lower() for n in names):
            return word
        for n in names:
            if abs(len(word) - len(n)) <= 2 and _difflib_names.SequenceMatcher(None, word.lower(), n.lower()).ratio() > 0.85:
                fixed.append(f"{word}->{n}")
                return n
        return word

    out = _re_polish.sub(r"\b[^\W\d_]{3,}\b", swap, text)
    if fixed:
        print(f"🎙️ heard names fixed: {', '.join(fixed)}", flush=True)
    return out


# 12 Nov 2026 (Elena): the EspaLuz map - a stranger who got the number from a friend learns who EspaLuz is, where she
# lives and how one family gets one memory. Sent the moment a new person arrives (before the first question) and on
# "mapa"/"map" (Telegram also /mapa).
# The menus are NOT changed. Only claims that are live today: no Android app (not public yet), no Russian classroom yet.
ESPALUZ_WHATSAPP_URL = "https://wa.me/50766623757"
ESPALUZ_TELEGRAM_URL = "https://t.me/EspaLuzFamily_bot"


def espaluz_map_text(platform: str) -> str:
    other = (f"📱 Also on Telegram: {ESPALUZ_TELEGRAM_URL} - the same EspaLuz." if platform == "whatsapp"
             else f"📱 Also on WhatsApp: {ESPALUZ_WHATSAPP_URL} - the same EspaLuz.")
    lines = [
        "🗺️ EspaLuz map",
        "",
        "EspaLuz is your family's bilingual friend for living your new country in Spanish: she remembers your family, "
        "speaks Spanish and English, and is with you right where life happens - the school gate, the doctor's office, "
        "the bank window, the bus, the neighbour at the door - any hour, day or night, on the go.",
        "",
        "Where I live",
        "💬 Here: write, send a voice note or a photo.",
        other,
        "🌐 app.espaluz.lat: your family dashboard and Pere & Titi's classroom for kids aged 6-7.",
        "",
        "One family, one memory",
        "Create your family at app.espaluz.lat → Connect → send me the code. Then the web, WhatsApp and Telegram all "
        "know your family.",
        "",
        ("👉 Tap /menu to see everything EspaLuz can do for you." if platform == "telegram"
         else f"👉 Type menu - or tap {ESPALUZ_WHATSAPP_URL}?text=menu - to see everything EspaLuz can do for you."),
        "Type mapa any time to see this map again.",
    ]
    return "\n".join(lines)
