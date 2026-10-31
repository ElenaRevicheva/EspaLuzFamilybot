import os
import random
import time
import uuid
import json
import requests
import subprocess
from datetime import datetime, timedelta
from gtts import gTTS
# Neural TTS for beautiful voices (Microsoft Edge)
try:
    from espaluz_neural_tts import generate_voice_sync
    NEURAL_TTS_AVAILABLE = True
    print("✓ Neural TTS loaded - beautiful voices enabled!")
except ImportError:
    NEURAL_TTS_AVAILABLE = False
    print("⚠️ Neural TTS not available, using gTTS fallback")
from dotenv import load_dotenv
import telebot
import re
from PIL import Image
import pytesseract
import io
import base64
import unicodedata
import math
import threading

# === Load environment variables ===
load_dotenv()

# === ENHANCED EMOTIONAL INTELLIGENCE MODULES (NEW - Jan 2026) ===
try:
    from espaluz_emotional_brain import (
        enhance_emotion_analysis,
        get_empathy_phrase,
        detect_user_type,
        track_activity,
        get_analytics_metrics,
        validate_org_code,
        analytics
    )
    from espaluz_country_contexts import (
        get_country_context,
        get_situation_phrases,
        detect_country_from_context,
        Country,
        COUNTRY_CONTEXTS
    )
    from espaluz_menu import (
        MENU_TEXT,
        WELCOME_SHORT,
        HELP_BANKING,
        HELP_MEDICAL,
        HELP_SCHOOL,
        HELP_SHOPPING,
        HELP_TRANSPORT,
        HELP_EMERGENCY,
        get_slang,
        SLANG_PANAMA,
        SLANG_MEXICO,
        SLANG_COLOMBIA,
        SLANG_ARGENTINA,
        SLANG_COSTA_RICA,
        TESTIMONIAL_7_DAY,
        TESTIMONIAL_30_DAY
    )
    ENHANCED_BRAIN_AVAILABLE = True
    print("✅ Enhanced emotional brain loaded successfully!")
except ImportError as e:
    ENHANCED_BRAIN_AVAILABLE = False
    print(f"⚠️ Enhanced brain modules not available: {e}")
    print("   Bot will work with basic functionality.")

# === PAYPAL & DEMO MODE MODULES (NEW - Jan 2026) ===
try:
    from espaluz_paypal_system import paypal_system, PAYPAL_SUBSCRIPTION_LINK
    from espaluz_demo_mode import demo_mode, detect_demo_emotion
    from espaluz_conversation_mode import conversation_mode, detect_language, get_opposite_language, get_quick_translate_prompt
    PAYPAL_SYSTEM_AVAILABLE = True
    print("✅ PayPal system and Demo mode loaded successfully!")
except ImportError as e:
    PAYPAL_SYSTEM_AVAILABLE = False
    paypal_system = None
    demo_mode = None
    PAYPAL_SUBSCRIPTION_LINK = "https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-6GR95409C95293139NFSBJJY"
    print(f"⚠️ PayPal/Demo modules not available: {e}")

# === PAGUELOFACIL ONE-TIME PAYMENTS (Panama / LATAM cards) ===
try:
    from espaluz_paguelofacil import paguelofacil_system, PAGUELOFACIL_AMOUNT
    PAGUELOFACIL_AVAILABLE = paguelofacil_system.is_configured()
    if PAGUELOFACIL_AVAILABLE:
        print("✅ PagueloFacil one-time payments configured")
    else:
        print("ℹ️ PagueloFacil module loaded — set PAGUELOFACIL_CCLW in .env to enable /pagar")
except ImportError as e:
    PAGUELOFACIL_AVAILABLE = False
    paguelofacil_system = None
    PAGUELOFACIL_AMOUNT = "11.00"
    print(f"⚠️ PagueloFacil module not available: {e}")

# === DATABASE MODULE (NEW - Jan 2026) ===
# PostgreSQL for investor-ready analytics - JSON fallback if unavailable
try:
    import espaluz_database as db
    DATABASE_AVAILABLE = db.db.use_database
    print(f"{'✅' if DATABASE_AVAILABLE else '⚠️'} Database: {'PostgreSQL connected' if DATABASE_AVAILABLE else 'Using JSON fallback'}")
except ImportError as e:
    DATABASE_AVAILABLE = False
    db = None
    print(f"⚠️ Database module not available: {e}")

# === UNIFIED MEMORY MODULE (NEW - Jan 2026) ===
# LangChain + PostgreSQL for cross-platform memory (Telegram + WhatsApp)
try:
    from espaluz_memory import EspaLuzMemory, LANGCHAIN_AVAILABLE
    UNIFIED_MEMORY_AVAILABLE = True
    print(f"✅ Unified memory loaded - LangChain: {LANGCHAIN_AVAILABLE}")
except ImportError as e:
    UNIFIED_MEMORY_AVAILABLE = False
    print(f"⚠️ Unified memory not available: {e}")

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
    print("✅ Enhancement module loaded (all 21 countries + 8 features)!")
except ImportError as e:
    ENHANCEMENTS_AVAILABLE = False
    print(f"⚠️ Enhancements not available: {e}")

# =============================================================================
# ONBOARDING SYSTEM (NEW - Jan 2026)
# Asks new users: Country -> Name -> Role -> Family members
# =============================================================================
ONBOARDING_FILE = "user_onboarding.json"

def load_onboarding_states():
    """Load onboarding states from file"""
    try:
        if os.path.exists(ONBOARDING_FILE):
            with open(ONBOARDING_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading onboarding states: {e}")
    return {}

def save_onboarding_states(states):
    """Save onboarding states to file"""
    try:
        with open(ONBOARDING_FILE, 'w') as f:
            json.dump(states, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error saving onboarding states: {e}")

# Onboarding states: {user_id: {step: "country|name|role|complete", country: "...", name: "...", role: "..."}}
onboarding_states = load_onboarding_states()

def get_user_onboarding(user_id):
    """Get user's onboarding state"""
    user_id = str(user_id)
    return onboarding_states.get(user_id, {"step": "country"})

def set_user_onboarding(user_id, data):
    """Update user's onboarding state"""
    user_id = str(user_id)
    onboarding_states[user_id] = data
    save_onboarding_states(onboarding_states)

def is_onboarding_complete(user_id):
    """Check if user has completed onboarding"""
    state = get_user_onboarding(user_id)
    return state.get("step") == "complete"

# Country detection from text
COUNTRY_KEYWORDS = {
    "panama": ["panama", "panamá", "панама", "pty"],
    "mexico": ["mexico", "méxico", "мексика", "cdmx"],
    "colombia": ["colombia", "колумбия", "bogota", "bogotá", "medellin", "medellín"],
    "argentina": ["argentina", "аргентина", "buenos aires"],
    "spain": ["spain", "españa", "испания", "madrid", "barcelona"],
    "costa_rica": ["costa rica", "коста рика", "san jose", "san josé"],
    "peru": ["peru", "perú", "перу", "lima"],
    "chile": ["chile", "чили", "santiago"],
    "ecuador": ["ecuador", "эквадор", "quito", "guayaquil"],
    "usa": ["usa", "united states", "сша", "америка", "miami", "new york", "los angeles"],
    "dominican": ["dominican", "dominicana", "república dominicana", "santo domingo"],
    "cuba": ["cuba", "куба", "havana"],
    "venezuela": ["venezuela", "венесуэла", "caracas"],
    "puerto_rico": ["puerto rico", "пуэрто рико"],
    "guatemala": ["guatemala", "гватемала"],
    "honduras": ["honduras", "гондурас"],
    "el_salvador": ["el salvador", "сальвадор"],
    "nicaragua": ["nicaragua", "никарагуа"],
    "bolivia": ["bolivia", "боливия"],
    "uruguay": ["uruguay", "уругвай"],
    "paraguay": ["paraguay", "парагвай"]
}

def detect_country_from_text(text):
    """Detect country from user's message"""
    text_lower = text.lower()
    for country, keywords in COUNTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return country
    return None

# Role detection from text
ROLE_KEYWORDS = {
    "parent": ["parent", "mother", "father", "mom", "dad", "мама", "папа", "madre", "padre", "mamá", "papá"],
    "child": ["child", "kid", "son", "daughter", "niño", "niña", "ребенок", "сын", "дочь"],
    "teenager": ["teenager", "teen", "adolescent", "подросток", "adolescente"],
    "traveler": ["traveler", "tourist", "travel", "viajero", "turista", "путешественник", "турист"],
    "expat": ["expat", "expatriate", "экспат", "relocating", "moved", "living abroad"],
    "local": ["local", "native", "local person", "trabajo", "service", "работа", "сервис"],
    "student": ["student", "estudent", "estudiante", "студент"]
}

def detect_role_from_text(text):
    """Detect user role from message"""
    text_lower = text.lower()
    for role, keywords in ROLE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return role
    return None

def finish_onboarding(user_id, message, onboarding):
    """Complete onboarding and set up user session"""
    # Create session if not exists
    if user_id not in user_sessions:
        user_sessions[user_id] = create_initial_session(user_id, message.from_user, message.chat)
    
    # Update session context with onboarding info
    prefs = user_sessions[user_id]["context"]["user"]["preferences"]
    prefs["country"] = onboarding.get("country", "panama")
    prefs["user_name"] = onboarding.get("name", "Friend")
    prefs["family_role"] = onboarding.get("role", "learner")
    
    # Store family members
    family_members = {}
    if onboarding.get("spouse"):
        family_members["spouse"] = onboarding["spouse"]
    if onboarding.get("children"):
        family_members["children"] = onboarding["children"]
    prefs["family_members"] = family_members
    
    # === SYNC TO UNIFIED DATABASE (Fix: Jan 22, 2026) ===
    if UNIFIED_MEMORY_AVAILABLE:
        try:
            memory = EspaLuzMemory(platform='telegram', platform_user_id=str(user_id))
            # Update user profile with onboarding data
            memory.update_user(
                display_name=onboarding.get("name"),
                current_country=onboarding.get("country"),
                user_type=onboarding.get("role", "expat")
            )
            # Store family members in unified DB (BOTH user_memories AND family_members tables)
            if family_members and (family_members.get("spouse") or family_members.get("children")):
                family_id = f"family_{user_id}"
                if family_members.get("spouse"):
                    # Store in user_memories for backward compatibility
                    memory.save_memory(f"Spouse: {family_members['spouse']}", "family", importance=8)
                    # Store in dedicated family_members table (PostgreSQL + LangChain)
                    memory.add_family(name=family_members['spouse'], relationship='spouse')
                    print(f"Added spouse to family_members table: {family_members['spouse']}")
                if family_members.get("children"):
                    for child in family_members["children"]:
                        # Store in user_memories for backward compatibility
                        memory.save_memory(f"Child: {child['name']}, age {child['age']}", "family", importance=8)
                        # Store in dedicated family_members table (PostgreSQL + LangChain)
                        memory.add_family(
                            name=child['name'], 
                            relationship='child', 
                            age=child.get('age'),
                            age_group=child.get('age_group', 'child')
                        )
                        print(f"Added child to family_members table: {child['name']}, age {child.get('age')}")
            print(f"✅ Onboarding synced to unified DB: {onboarding.get('name')} from {onboarding.get('country')}")
        except Exception as e:
            print(f"⚠️ DB sync error (non-fatal): {e}")
    
    # Build family line for completion message
    family_line = ""
    if family_members:
        parts = []
        if family_members.get("spouse"):
            parts.append(f"💑 {family_members['spouse']}")
        if family_members.get("children"):
            kids = [f"{c['name']} ({c['age']})" for c in family_members["children"]]
            parts.append(f"👶 Kids: {', '.join(kids)}")
        family_line = "👨‍👩‍👧 Family: " + " | ".join(parts) if parts else ""
    
    # Send completion message
    msg = ONBOARDING_MESSAGES["complete"].format(
        name=onboarding.get("name", "Friend"),
        country=onboarding.get("country", "your country").replace("_", " ").title(),
        role=onboarding.get("role", "learner").title(),
        family_line=family_line
    )
    bot.send_message(message.chat.id, msg)

ONBOARDING_MESSAGES = {
    "country": """👋 Welcome to EspaLuz!

🌍 First, where are you located or planning to travel?

I support 21 Spanish-speaking countries + USA!

Examples:
• "Panama" 🇵🇦
• "Mexico" 🇲🇽
• "Colombia" 🇨🇴
• "Spain" 🇪🇸
• "Costa Rica" 🇨🇷
• Or any other country!

Just type your country name...""",
    
    "name": """Great! 🎉

Now, what's your name? (I'll personalize our conversations)

Just type your first name...""",
    
    "role": """Nice to meet you, {name}! 👋

What best describes you?

• "Parent" - Learning with my family
• "Child/Teen" - I'm young and learning
• "Traveler" - I'm visiting Spanish-speaking countries
• "Expat" - I moved abroad recently
• "Local" - I want to improve my English for work
• "Student" - I'm studying languages

Just type what fits you best...""",

    "family_spouse": """👨‍👩‍👧 Tell me about your family, {name}!

Are you married or have a partner?

• "Married to [name]" or "Partner [name]"
• "Single parent"
• "Skip" - I'll ask later

Example: "Married to Alex" """,

    "family_children": """👶 Do you have children? (I'll personalize learning for them too!)

Tell me their names and ages:
• "Sofia 8, Marco 5"
• "One daughter, Ana, 12"
• "No children" or "Skip"

Example: "Alisa 4, no more kids" """,

    "family_complete": """👨‍👩‍👧‍👦 Wonderful! I now know your family:

{family_summary}

I'll remember everyone and personalize our learning journey! 🌟""",

    "complete": """🎉 Perfect! You're all set, {name}!

📍 Country: {country}
👤 Role: {role}
{family_line}

Now I'll adapt my teaching to YOUR real-life situations in {country}!

Try:
• Send a voice message 🎤
• Take a photo of text 📷
• Just type anything to chat!

/help - See all commands
/menu - Full feature list

¡Empecemos! Let's begin! 🚀"""
}

# === Configuration ===
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
CLAUDE_MODEL = (os.environ.get("CLAUDE_MODEL_NAME", "").strip() or "claude-sonnet-4-6")
CLAUDE_API_VERSION = os.environ.get("CLAUDE_API_VERSION", "2023-06-01")
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", 10))


def _groq_model() -> str:
    """Groq model id, resolved at CALL time.

    Groq retires llama-3.3-70b-versatile in August 2026. Keeping the id behind
    GROQ_MODEL makes that migration a one-line .env change plus a restart,
    instead of hunting hard-coded strings. Read lazily (not at import) so the
    value is picked up on restart without a code deploy.
    """
    # Default updated 2026-08-16: llama-3.3-70b-versatile was SHUT DOWN that day
    # (so was llama-3.1-8b-instant). Leaving a retired id as the fallback default
    # meant this only worked because GROQ_MODEL happens to be set in .env — one
    # missing env var away from calling a model that no longer exists.
    return os.environ.get("GROQ_MODEL", "").strip() or "openai/gpt-oss-120b"

# === WEBHOOK KILLER THREAD ===
def webhook_killer_thread():
    print("🔥🔥🔥 WEBHOOK KILLER THREAD STARTING 🔥🔥🔥")
    webhook_check_interval = 30
    killer_cycle = 0

    while True:
        try:
            killer_cycle += 1
            print(f"🛡️ Webhook killer check cycle #{killer_cycle}")

            delete_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook?drop_pending_updates=true"
            info_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"

            delete_response = requests.get(delete_url, timeout=30)
            delete_result = delete_response.json()
            print(f"🧹 Webhook deletion result: {delete_result}")

            info_response = requests.get(info_url, timeout=30)
            webhook_info = info_response.json()
            webhook_url = webhook_info.get('result', {}).get('url', '')

            if webhook_url:
                print(f"⚠️ WARNING: Webhook still exists: {webhook_url}! Trying again...")
            else:
                print(f"✅ No webhook found in cycle #{killer_cycle}")

            time.sleep(webhook_check_interval)
        except Exception as e:
            print(f"❌ Webhook killer error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(60)

# === FFmpeg Check and Debug Paths ===
print("Checking FFmpeg installation...")

try:
    ffmpeg_result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
    ffmpeg_version = ffmpeg_result.stdout.split('\n')[0] if ffmpeg_result.stdout else "Unknown version"
    print(f"✅ FFmpeg is available: {ffmpeg_version}")

    ffprobe_result = subprocess.run(["ffprobe", "-version"], capture_output=True, text=True, check=True)
    ffprobe_version = ffprobe_result.stdout.split('\n')[0] if ffprobe_result.stdout else "Unknown version"
    print(f"✅ FFprobe is available: {ffprobe_version}")
    FFMPEG_AVAILABLE = True
except Exception as e:
    print(f"❌ FFmpeg check failed: {str(e)}")
    FFMPEG_AVAILABLE = False

def create_test_video():
    base_video = "espaluz_loop.mp4"
    if not os.path.exists(base_video) and FFMPEG_AVAILABLE:
        print("Base video not found, creating a simple test video...")
        try:
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", "color=c=blue:s=640x480:d=5",
                "-c:v", "libx264",
                base_video
            ], check=True, capture_output=True)

            if os.path.exists(base_video):
                print(f"✅ Created test video: {base_video}")
            else:
                print("❌ Failed to create test video")
        except Exception as e:
            print(f"❌ Error creating test video: {str(e)}")

def debug_file_paths():
    base_video = "espaluz_loop.mp4"
    base_video_abs = os.path.abspath(base_video)
    print("\n=== DEBUGGING INFO ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Base video relative path: {base_video}")
    print(f"Base video absolute path: {base_video_abs}")
    print(f"Base video exists: {os.path.exists(base_video_abs)}")
    files = os.listdir(".")
    print(f"Files in current directory: {files}")
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
        print(f"FFmpeg version: {result.stdout.splitlines()[0]}")
    except Exception as e:
        print(f"FFmpeg check error: {e}")
    print("====================\n")

def clean_text_for_speech(text: str) -> str:
    """Remove punctuation marks, formatting AND EMOJIS for natural speech"""
    # FIRST: Remove ALL emojis (so they're not pronounced!)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed characters
        "\U0001F1E0-\U0001F1FF"  # Flags
        "\U00002600-\U000026FF"  # Misc symbols (sun, stars, etc)
        "\U00002700-\U000027BF"  # Dingbats
        "\U0000FE00-\U0000FE0F"  # Variation Selectors
        "\U0001F000-\U0001F02F"  # Mahjong
        "\U0001F0A0-\U0001F0FF"  # Playing cards
        "\U00002B50"              # Star
        "\U00002705"              # Check mark
        "\U0000274C"              # X mark
        "\U0001F4A1"              # Lightbulb
        "\U0001F5E3"              # Speaking head
        "\U0001F4D6"              # Book
        "\U0001F30E"              # Globe
        "\U0001F3AF"              # Target
        "]+"
    , re.UNICODE)
    text = emoji_pattern.sub('', text)
    
    # Remove markdown formatting
    text = re.sub(r'\*+([^*]+)\*+', r'\1', text)  # Remove asterisks
    text = re.sub(r'_+([^_]+)_+', r'\1', text)    # Remove underscores
    text = re.sub(r'`+([^`]+)`+', r'\1', text)    # Remove backticks
    
    # Remove quotes but keep the content
    text = re.sub(r'"([^"]+)"', r'\1', text)
    text = re.sub(r"'([^']+)'", r'\1', text)
    
    # Remove numbers in lists (1. 2. etc)
    text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n\d+\.\s*', '\n', text)
    
    # Remove emoji numbers
    text = re.sub(r'[0-9]️⃣', '', text)
    
    # Remove other common symbols but keep sentence flow
    text = re.sub(r'[#@\[\](){}<>]', '', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Call startup checks
create_test_video()
debug_file_paths()

# === SUPABASE INTEGRATION FUNCTIONS ===
# The EspaLuz web app (dashboard + kids classroom) runs on this Supabase project. These calls were stubbed out in Jan
# 2026 on the belief that the project was gone; it is live, so a linked user's dashboard showed nothing from Telegram.
# Re-enabled 31 Oct 2026. They run in a background thread (see sync_progress_to_saas): the web never slows a reply.
SAAS_FUNCTIONS_URL = "https://euyidvolwqmzijkfrplh.supabase.co/functions/v1"


def track_telegram_conversation(user_id, user_message, bot_reply, session_data):
    """Track Telegram conversation in Supabase database (404 = this Telegram user never linked the web app)."""
    try:
        learning_progress = session_data.get("context", {}).get("learning", {}).get("progress", {})
        emotional_state = session_data.get("context", {}).get("emotional_state", {})
        user_preferences = session_data.get("context", {}).get("user", {}).get("preferences", {})
        
        vocabulary_learned = extract_conversation_vocabulary(user_message, bot_reply)
        message_count = session_data.get("context", {}).get("conversation", {}).get("message_count", 1)
        estimated_duration = min(max(message_count * 0.5, 1), 30)
        
        session_payload = {
            "platform_user_id": str(user_id),
            "platform": "telegram",
            "session_type": "conversation",
            "source": "telegram_bot",
            "content": {
                "user_message": user_message[:500],
                "bot_response": bot_reply[:500],
                "family_role": user_preferences.get("family_role", "unknown"),
                "emotional_state": emotional_state.get("current_emotion", "neutral"),
                "message_count": message_count
            },
            "progress_data": {
                "vocabulary_learned": vocabulary_learned,
                "spanish_words_total": len(learning_progress.get("vocabulary", {}).get("spanish", {}).get("learned", [])),
                "grammar_points_total": len(learning_progress.get("grammar", {}).get("spanish", {}).get("learned", [])),
                "learning_level": user_preferences.get("learning_level", "beginner"),
                "session_emotions": emotional_state.get("last_emotions", [])
            },
            "emotional_tone": emotional_state.get("current_emotion", "neutral"),
            "duration_minutes": estimated_duration
        }
        
        response = requests.post(
            f"{SAAS_FUNCTIONS_URL}/submit-progress",
            json=session_payload,
            headers={
                "Authorization": f"Bearer {os.environ.get('SUPABASE_ANON_KEY')}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Telegram conversation tracked for user {user_id}")
            return True
        elif response.status_code == 404:
            return False  # not linked to the web app - nothing to sync
        else:
            print(f"⚠️ Failed to track conversation: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error tracking Telegram conversation: {e}")
        return False

def extract_conversation_vocabulary(user_message, bot_reply):
    """Extract vocabulary words from this specific conversation"""
    import re
    
    vocabulary = []
    spanish_pattern = r'\b[a-záéíóúñü]{3,}\b'
    spanish_words = re.findall(spanish_pattern, bot_reply.lower())
    
    english_common = {'the', 'and', 'you', 'are', 'for', 'not', 'can', 'use', 'get', 'see', 'new', 'way'}
    spanish_words = [word for word in spanish_words if word not in english_common]
    
    vocabulary = list(set(spanish_words))[:5]
    return vocabulary

def update_connected_bot_activity(user_id):
    """Update last activity timestamp for connected bot (re-enabled 31 Oct 2026, see SAAS_FUNCTIONS_URL)."""
    try:
        payload = {
            "telegram_user_id": str(user_id),
            "last_activity": datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{SAAS_FUNCTIONS_URL}/update-bot-activity",
            json=payload,
            headers={
                "Authorization": f"Bearer {os.environ.get('SUPABASE_ANON_KEY')}",
                "Content-Type": "application/json"
            },
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✅ Updated activity for user {user_id}")
        elif response.status_code != 404:
            print(f"⚠️ Failed to update activity: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error updating bot activity: {e}")

def sync_progress_to_saas(user_id, user_message, bot_reply, session_data):
    """Both web calls, off the reply path."""
    def _run():
        if track_telegram_conversation(user_id, user_message, bot_reply, session_data):
            update_connected_bot_activity(user_id)
    threading.Thread(target=_run, daemon=True).start()

# === TELEBOT SETUP ===


# =============================================================================
# STRIP ASTERISKS FROM AI RESPONSES (Force clean formatting)
# =============================================================================

def strip_emojis(text: str) -> str:
    """Remove ALL emojis from text (for TTS so they're not pronounced)"""
    import re
    # Comprehensive emoji pattern covering all Unicode emoji ranges
    emoji_pattern = re.compile(
        "["
        "😀-🙏"  # emoticons
        "🌀-🗿"  # symbols & pictographs
        "🚀-🛿"  # transport & map symbols
        "🜀-🝿"  # alchemical symbols
        "🞀-🟿"  # Geometric Shapes Extended
        "🠀-🣿"  # Supplemental Arrows-C
        "🤀-🧿"  # Supplemental Symbols and Pictographs
        "🨀-🩯"  # Chess Symbols
        "🩰-🫿"  # Symbols and Pictographs Extended-A
        "✂-➰"  # Dingbats
        "Ⓜ-🉑"  # Enclosed characters
        "🇠-🇿"  # Flags
        "☀-⛿"  # Misc symbols (sun, stars, etc)
        "✀-➿"  # Dingbats
        "︀-️"  # Variation Selectors
        "🀀-🀯"  # Mahjong
        "🂠-🃿"  # Playing cards
        "✅❌💡🗣️📖🌎🎯☕🎓🏖️"  # Common ones we use
        "]+"
    , re.UNICODE)
    return emoji_pattern.sub('', text).strip()


def strip_markdown_formatting(text: str) -> str:
    """Remove **bold** and *italic* markdown from text"""
    import re
    # Remove **bold** -> bold
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    # Remove *italic* -> italic (but not inside words)
    text = re.sub(r'(?<![\w])\*([^*]+)\*(?![\w])', r'\1', text)
    # Remove any remaining double asterisks
    text = text.replace('**', '')
    return text

# =============================================================================
# NEURAL TTS WRAPPER - Use this instead of gTTS directly
# =============================================================================
def generate_speech(text: str, lang: str = "es", message_id=None) -> str:
    """
    Generate speech using Neural TTS (beautiful) or gTTS (fallback).
    Returns path to audio file.
    """
    import os
    temp_path = f"speech_{message_id or hash(text) % 100000}.mp3"
    
    # Try Neural TTS first (beautiful Microsoft voices)
    if NEURAL_TTS_AVAILABLE:
        try:
            result = generate_voice_sync(text, lang=lang, style="tutor", message_id=message_id)
            if result and os.path.exists(result):
                return result
        except Exception as e:
            print(f"Neural TTS failed, falling back to gTTS: {e}")
    
    # Fallback to gTTS
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(temp_path)
        return temp_path
    except Exception as e:
        print(f"gTTS also failed: {e}")
        return None


bot = telebot.TeleBot(TELEGRAM_TOKEN)

# =============================================================================
# 💾 PERSISTENT SESSION STORAGE (NEW - Upgrade #3)
# =============================================================================
SESSIONS_FILE = "user_sessions.json"

def load_persistent_sessions():
    """Load user sessions from persistent storage."""
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
                sessions = json.load(f)
                print(f"💾 Loaded {len(sessions)} user sessions from disk")
                return sessions
    except Exception as e:
        print(f"⚠️ Error loading sessions (starting fresh): {e}")
    return {}

def save_persistent_sessions():
    """Save user sessions to persistent storage."""
    global user_sessions
    try:
        # Create a serializable copy (remove non-serializable items)
        serializable_sessions = {}
        for user_id, session in user_sessions.items():
            try:
                # Test if serializable
                json.dumps(session)
                serializable_sessions[user_id] = session
            except (TypeError, ValueError):
                # Skip non-serializable sessions
                print(f"⚠️ Session for {user_id} not serializable, skipping")
        
        with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(serializable_sessions, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved {len(serializable_sessions)} user sessions to disk")
    except Exception as e:
        print(f"⚠️ Error saving sessions: {e}")

def auto_save_sessions():
    """Background thread to auto-save sessions every 5 minutes."""
    while True:
        time.sleep(300)  # 5 minutes
        try:
            save_persistent_sessions()
        except Exception as e:
            print(f"⚠️ Auto-save error: {e}")

# Load existing sessions from disk
user_sessions = load_persistent_sessions()

# Start auto-save thread
session_save_thread = threading.Thread(target=auto_save_sessions, daemon=True)
session_save_thread.start()
print("💾 Session auto-save started (every 5 minutes)")

# === Start webhook killer in background ===
webhook_thread = threading.Thread(target=webhook_killer_thread, daemon=True)
webhook_thread.start()
print("🛡️ Webhook killer thread started in background")

# === GUMROAD SYNC FUNCTION ===
def poll_subscriptions():
    """Poll Gumroad API and update local subscriber list"""
    # DISABLED: Gumroad is suspended - Jan 2026
    print("⏸️ Gumroad polling DISABLED (suspended)")
    return
    try:
        GUMROAD_API_KEY = os.environ.get("GUMROAD_API_KEY")
        GUMROAD_PRODUCT_ID = os.environ.get("GUMROAD_PRODUCT_ID")
        url = f"https://api.gumroad.com/v2/subscriptions?product_id={GUMROAD_PRODUCT_ID}"
        headers = {"Authorization": f"Bearer {GUMROAD_API_KEY}"}

        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"❌ Gumroad error {res.status_code}: {res.text}")
            return

        data = res.json()
        if not data.get("success"):
            print(f"❌ Gumroad failure: {data}")
            return

        updated = {}
        for sub in data.get("subscriptions", []):
            email = sub.get("email", "").lower()
            status = "active" if sub.get("status") == "active" else "inactive"
            updated[email] = {
                "telegram_id": None,
                "status": status
            }

        with open("subscribers.json", "w") as f:
            json.dump(updated, f, indent=2)

        print(f"✅ Subscription database updated. Total: {len(updated)}")

    except Exception as e:
        print(f"❌ Exception polling Gumroad: {e}")

def is_subscribed(user_id):
    """
    Iron-clad access check: trial, PagueloFacil prepaid, or PayPal subscription.
    No grace period — expired users must pay to continue learning.
    """
    user_id = str(user_id)

    if PAYPAL_SYSTEM_AVAILABLE and paypal_system:
        return paypal_system.is_user_allowed(user_id)["allowed"]

    # Fallback when PayPal system unavailable
    try:
        from espaluz_paguelofacil import has_active_access
        if has_active_access(user_id):
            return True
    except ImportError:
        pass

    try:
        with open("subscribers.json", "r") as f:
            subscribers = json.load(f)
        for email, info in subscribers.items():
            if str(info.get("telegram_id")) == str(user_id) and info.get("status") == "active":
                return True
    except Exception as e:
        print(f"⚠️ Legacy subscription check error: {e}")

    return False


def _reply_markdown_or_plain(message, text):
    """30 Oct 2026: the pause message carries the PayPal link (plan_id=...), and an underscore opens Markdown italics
    that never close -> Telegram 400 "can't parse entities" -> the lapsed user got SILENCE instead of the pay link.
    Markdown when Telegram accepts it, the same words as plain text when it does not."""
    try:
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        print(f"⚠️ Markdown rejected ({e}); sending plain text")
        bot.reply_to(message, text.replace("**", "").replace("*", ""))


def enforce_learning_access(message, user_id: str) -> bool:
    """
    Gate tutor/voice/photo learning. Sends pause message if blocked;
    sends expiry reminders when access is active but nearing end.
    """
    user_id = str(user_id)
    if not PAYPAL_SYSTEM_AVAILABLE or not paypal_system:
        if not is_subscribed(user_id):
            bot.reply_to(
                message,
                "🔐 Tu viaje de aprendizaje está en pausa. / Your learning journey is paused.\n\n"
                "Envía /pagar o /subscribe para continuar. / Send /pagar or /subscribe to continue.",
            )
            return False
        return True

    result = paypal_system.is_user_allowed(user_id)
    if not result["allowed"]:
        _reply_markdown_or_plain(message, result["message"])
        return False

    reminder = paypal_system.get_payment_reminder_message(user_id, result)
    if reminder:
        _reply_markdown_or_plain(message, reminder)
    return True

# === EMOTIONAL INTELLIGENCE & PERSONALIZATION ===
FAMILY_MEMBERS = {
    "alisa": {
        "role": "child",
        "age": 6,  # Elena: ages 5-7 (22 Oct 2026), then 6-7, not toddlers (30 Oct 2026)
        "age_range": "6-7",
        "learning_level": "beginner",
        "interests": ["animals", "colors", "games", "songs", "movement games", "Panama"],
        "tone": "playful",
        "language_balance": {"spanish": 0.6, "english": 0.4},
        "russian_variants": ["алиса", "алисочка", "алисa"]
    },
    "marina": {
        "role": "elder",
        "age": 65,
        "learning_level": "beginner",
        "interests": ["cooking", "culture", "daily life", "health"],
        "tone": "patient",
        "language_balance": {"spanish": 0.7, "english": 0.3},
        "russian_variants": ["марина", "маринa"]
    },
    "elena": {
        "role": "parent",
        "age": 39,
        "learning_level": "intermediate",
        "interests": ["work", "travel", "parenting", "culture"],
        "tone": "conversational",
        "language_balance": {"spanish": 0.5, "english": 0.5},
        "russian_variants": ["елена", "еленa", "лена"]
    }
}

def detect_emotion(text):
    """Simple emotion detection from text"""
    emotions = {
        "happy": ["happy", "glad", "joy", "excited", "feliz", "contento", "alegre", "радость", "счастье", "рада", "рад", "!"],
        "sad": ["sad", "upset", "unhappy", "triste", "грустно", "печально", ":("],
        "confused": ["confused", "don't understand", "no entiendo", "confundido", "не понимаю", "путаюсь", "confused"],
        "frustrated": ["frustrated", "annoyed", "molesto", "frustrado", "разочарован", "раздражен"],
        "curious": ["curious", "wonder", "interesting", "curioso", "interesante", "любопытно", "интересно", "?"]
    }

    text_lower = text.lower()
    detected = {"curious": 0.2}  # Default low-level curiosity

    for emotion, keywords in emotions.items():
        for keyword in keywords:
            if keyword in text_lower:
                detected[emotion] = detected.get(emotion, 0) + 0.3

    # Find dominant emotion
    dominant = max(detected.items(), key=lambda x: x[1]) if detected else ("neutral", 1.0)
    return dominant[0], detected

def enhanced_emotion_detection(text, session):
    """Advanced emotion detection with learning capabilities - NOW WITH ENHANCED BRAIN!"""
    user_id = str(session.get("user_id", "unknown"))
    
    # Start with the current keyword-based approach
    base_emotion, emotion_data = detect_emotion(text)

    # Add contextual analysis
    contextual_emotion = analyze_emotional_context(text, session)

    # Add language-specific emotion cues
    language_specific = detect_language_specific_emotions(text)

    # Combine emotion signals with weighted confidence
    combined_emotions = {}

    # Base detection (50% weight)
    for emotion, value in emotion_data.items():
        combined_emotions[emotion] = value * 0.5

    # Contextual (30% weight)
    for emotion, value in contextual_emotion.items():
        if emotion in combined_emotions:
            combined_emotions[emotion] += value * 0.3
        else:
            combined_emotions[emotion] = value * 0.3

    # Language-specific (20% weight)
    for emotion, value in language_specific.items():
        if emotion in combined_emotions:
            combined_emotions[emotion] += value * 0.2
        else:
            combined_emotions[emotion] = value * 0.2

    # Find dominant emotion from basic detection
    dominant = max(combined_emotions.items(), key=lambda x: x[1]) if combined_emotions else ("neutral", 1.0)
    basic_emotion = dominant[0]
    basic_confidence = dominant[1] / sum(combined_emotions.values()) if sum(combined_emotions.values()) > 0 else 0.5

    # =========================================================================
    # 🧠 ENHANCED EMOTIONAL BRAIN INTEGRATION (NEW!)
    # =========================================================================
    enhanced_result = None
    response_strategy = None
    empathy_phrase = ""
    is_expat_emotion = False
    
    if ENHANCED_BRAIN_AVAILABLE:
        try:
            # Call the enhanced emotion analysis from espaluz_emotional_brain
            enhanced_result = enhance_emotion_analysis(text, user_id, basic_emotion)
            
            # If enhanced brain has higher confidence, use its result
            if enhanced_result and enhanced_result.get("confidence", 0) > basic_confidence:
                dominant = (enhanced_result["dominant_emotion"], enhanced_result["confidence"])
                
                # Get the response strategy for this emotion
                response_strategy = enhanced_result.get("strategy", {})
                
                # Get empathy phrase in both languages
                empathy_phrase = get_empathy_phrase(enhanced_result["dominant_emotion"], "en")
                
                # Check if this is an expat-specific emotion
                expat_emotions = [
                    "homesickness", "cultural_shock", "language_frustration", 
                    "language_anxiety", "language_breakthrough", "social_isolation",
                    "child_adaptation_worry", "urgency_stress", "cultural_confusion",
                    "integration_anxiety", "family_separation_grief"
                ]
                is_expat_emotion = enhanced_result["dominant_emotion"] in expat_emotions
                
                print(f"🧠 Enhanced brain detected: {enhanced_result['dominant_emotion']} (conf: {enhanced_result['confidence']:.2f})")
        except Exception as e:
            print(f"⚠️ Enhanced brain error (using basic): {e}")

    # Add confidence metric
    confidence = dominant[1] if isinstance(dominant[1], float) else basic_confidence

    # Add emotional progression analysis
    progression_analysis = analyze_emotional_progression(dominant[0], session)

    return {
        "dominant_emotion": dominant[0],
        "confidence": confidence,
        "emotion_data": combined_emotions,
        "progression": progression_analysis,
        # Enhanced brain additions
        "enhanced_result": enhanced_result,
        "response_strategy": response_strategy,
        "empathy_phrase": empathy_phrase,
        "is_expat_emotion": is_expat_emotion
    }

def analyze_emotional_context(text, session):
    """Analyze emotional context based on conversation history"""
    # Initialize with neutral emotion
    contextual_emotions = {"neutral": 0.5}

    if "messages" not in session or not session["messages"]:
        return contextual_emotions

    # Get last few messages
    recent_messages = session["messages"][-3:]
    if not recent_messages:
        return contextual_emotions

    # Check for emotion patterns
    consecutive_questions = sum(1 for msg in recent_messages 
                              if "content" in msg and 
                              isinstance(msg["content"], str) and 
                              msg["content"].strip().endswith("?"))
    if consecutive_questions >= 2:
        contextual_emotions["curious"] = 0.7

    # Check for short, frustrated responses
    short_responses = sum(1 for msg in recent_messages 
                         if msg.get("role") == "user" and 
                         "content" in msg and 
                         isinstance(msg["content"], str) and 
                         len(msg["content"].split()) < 5)
    if short_responses >= 2:
        contextual_emotions["frustrated"] = 0.6

    # Check for enthusiasm markers
    enthusiasm_markers = sum(1 for msg in recent_messages 
                            if msg.get("role") == "user" and 
                            "content" in msg and 
                            isinstance(msg["content"], str) and 
                            "!" in msg["content"])
    if enthusiasm_markers >= 2:
        contextual_emotions["happy"] = 0.7

    return contextual_emotions

def detect_language_specific_emotions(text):
    """Detect emotions based on language-specific cues"""
    text_lower = text.lower()
    language_emotions = {"neutral": 0.3}

    # Russian emotional cues
    russian_happy = ["отлично", "класс", "здорово", "супер"]
    russian_sad = ["грустно", "жаль", "печально"]
    russian_confused = ["не понимаю", "не ясно", "запутался"]

    # Spanish emotional cues
    spanish_happy = ["genial", "excelente", "maravilloso", "fantástico"]
    spanish_sad = ["triste", "lástima", "pena"]
    spanish_confused = ["confundido", "no entiendo", "no comprendo"]

    # Check Russian cues
    if any(cue in text_lower for cue in russian_happy):
        language_emotions["happy"] = 0.8
    if any(cue in text_lower for cue in russian_sad):
        language_emotions["sad"] = 0.8
    if any(cue in text_lower for cue in russian_confused):
        language_emotions["confused"] = 0.8

    # Check Spanish cues
    if any(cue in text_lower for cue in spanish_happy):
        language_emotions["happy"] = 0.8
    if any(cue in text_lower for cue in spanish_sad):
        language_emotions["sad"] = 0.8
    if any(cue in text_lower for cue in spanish_confused):
        language_emotions["confused"] = 0.8

    return language_emotions

def analyze_emotional_progression(current_emotion, session):
    """Analyze emotional progression over time"""
    if "context" not in session or "emotional_state" not in session["context"]:
        return "stable"

    # Get recent emotion history
    emotions = session["context"]["emotional_state"].get("last_emotions", [])
    if not emotions:
        return "stable"

    # Check for improvement patterns
    negative_emotions = ["sad", "confused", "frustrated"]
    positive_emotions = ["happy", "curious"]

    if len(emotions) >= 3:
        # Improvement pattern: negative -> neutral/positive
        if emotions[0] in negative_emotions and emotions[-1] in positive_emotions:
            return "improving"

        # Worsening pattern: positive -> negative
        if emotions[0] in positive_emotions and emotions[-1] in negative_emotions:
            return "worsening"

        # Consistent negative pattern
        if all(emotion in negative_emotions for emotion in emotions[-3:]):
            return "consistently_negative"

        # Consistent positive pattern
        if all(emotion in positive_emotions for emotion in emotions[-3:]):
            return "consistently_positive"

    # Default to stable if no clear pattern
    return "stable"

def calibrate_emotional_response(session, detected_emotion, message_content):
    """Create sophisticated emotional calibration for responses"""

    # Analyze emotional progression
    emotion_history = session["context"]["emotional_state"]["last_emotions"]

    # Detect emotional patterns
    if len(emotion_history) >= 3:
        if all(emotion == "frustrated" for emotion in emotion_history[-3:]):
            # Frustration pattern detected
            return {
                "response_tone": "extra_supportive",
                "simplify_content": True,
                "offer_encouragement": True,
                "suggest_break": True,
                "emotional_priority": "confidence_building"
            }

        if emotion_history[-3:] == ["confused", "frustrated", "frustrated"]:
            # Learning difficulty pattern
            return {
                "response_tone": "patient_teaching",
                "simplify_content": True,
                "repeat_core_concepts": True,
                "provide_examples": True,
                "emotional_priority": "clarity"
            }

    # Check for sentiment shifts
    if len(emotion_history) >= 2:
        current = detected_emotion
        previous = emotion_history[-1]

        if previous == "happy" and current in ["sad", "frustrated"]:
            # Positive to negative shift
            return {
                "response_tone": "empathetic",
                "acknowledge_change": True,
                "offer_support": True,
                "emotional_priority": "validation"
            }

        if previous in ["sad", "frustrated"] and current == "happy":
            # Negative to positive shift
            return {
                "response_tone": "celebratory",
                "reinforce_progress": True,
                "emotional_priority": "momentum"
            }

    # Default emotional calibration based on current emotion
    emotion_calibration = {
        "happy": {
            "response_tone": "matching_enthusiasm",
            "content_depth": "increase",
            "challenge_level": "increase",
            "emotional_priority": "engagement"
        },
        "sad": {
            "response_tone": "warm_supportive",
            "content_depth": "maintain",
            "challenge_level": "decrease",
            "emotional_priority": "comfort"
        },
        "confused": {
            "response_tone": "clear_patient",
            "content_depth": "decrease",
            "challenge_level": "decrease",
            "simplify_explanation": True,
            "emotional_priority": "clarity"
        },
        "frustrated": {
            "response_tone": "calm_encouraging",
            "content_depth": "decrease",
            "challenge_level": "decrease",
            "offer_alternative": True,
            "emotional_priority": "reassurance"
        },
        "curious": {
            "response_tone": "engaging_informative",
            "content_depth": "increase",
            "challenge_level": "maintain",
            "provide_details": True,
            "emotional_priority": "knowledge"
        }
    }

    return emotion_calibration.get(detected_emotion, {
        "response_tone": "neutral_supportive",
        "content_depth": "maintain",
        "challenge_level": "maintain",
        "emotional_priority": "communication"
    })

def detect_family_member(user_info, message_text=""):
    """Detect which family member is speaking based on name, patterns and previous interactions"""
    first_name = user_info.first_name.lower() if user_info.first_name else ""
    message_lower = message_text.lower()

    # Check for explicit identification in the message
    if "soy alisa" in message_lower or "я алиса" in message_lower:
        return "alisa"
    elif "soy marina" in message_lower or "я марина" in message_lower:
        return "marina"
    elif "soy elena" in message_lower or "я елена" in message_lower:
        return "elena"

    # Check against known names and variants
    for member, info in FAMILY_MEMBERS.items():
        if member in first_name:
            return member
        for variant in info["russian_variants"]:
            if variant in first_name:
                return member

    # Check message patterns
    if any(word in message_lower for word in ["мама", "mama", "mother"]):
        return "elena"
    elif any(word in message_lower for word in ["бабушка", "abuela", "grandmother"]):
        return "marina"
    elif any(word in message_lower for word in ["дочь", "hija", "daughter"]) or len(message_lower.split()) < 3:
        return "alisa"

    # Default to elena if we can't determine
    return "elena"

def identify_language_learning_content(text, family_member):
    """Extract words or phrases that should be tracked as learning progress"""
    learned_items = {
        "spanish_words": [],
        "english_words": [],
        "needs_review": [],
        "grammar_points": []
    }

    # Spanish word pattern (simple approach)
    spanish_words = re.findall(r'\b[a-záéíóúñ]{3,}\b', text.lower())
    english_words = re.findall(r'\b[a-z]{3,}\b', text.lower())

    # Filter to likely Spanish-only words
    spanish_markers = ['ñ', 'á', 'é', 'í', 'ó', 'ú']

    for word in spanish_words:
        if any(marker in word for marker in spanish_markers):
            learned_items["spanish_words"].append(word)

    # Simple grammar pattern detection
    if "por vs para" in text.lower():
        learned_items["grammar_points"].append("por_vs_para")
    elif "ser vs estar" in text.lower():
        learned_items["grammar_points"].append("ser_vs_estar")

    # Limit to recent words based on level
    member_info = FAMILY_MEMBERS.get(family_member, FAMILY_MEMBERS["elena"])
    if member_info["learning_level"] == "beginner":
        learned_items["spanish_words"] = learned_items["spanish_words"][:3]
        learned_items["english_words"] = learned_items["english_words"][:3]

    return learned_items

def enhance_language_learning_detection(text, family_member, session):
    """Enhanced detection of language learning content with context awareness"""
    # Start with basic detection
    basic_items = identify_language_learning_content(text, family_member)

    # Add more sophisticated grammar pattern detection
    grammar_patterns = {
        "past_tense": [r'\b(ayer|pasado).+\b(é|aste|ó|amos|aron)\b', r'\b\w+(é|aste|ó|amos|aron)\b'],
        "future_tense": [r'\b(mañana|futuro).+\b\w+(ré|rás|rá|remos|rán)\b', r'\b\w+(ré|rás|rá|remos|rán)\b'],
        "subjunctive": [r'\bque \w+(e|es|a|an|emos)\b', r'\bsi \w+(era|ese|ara)\b'],
        "commands": [r'\b\w+(a|e|ad|ed)(!| ahora| por favor)\b'],
        "conditional": [r'\b\w+(ría|rías|ría|ríamos|rían)\b']
    }

    for point, patterns in grammar_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text.lower()):
                basic_items["grammar_points"].append(point)
                break

    # Detect idioms and expressions
    spanish_idioms = [
        "poco a poco", "de vez en cuando", "más o menos", "en seguida", 
        "hacer caso", "tener ganas", "dar la vuelta", "echar de menos"
    ]

    for idiom in spanish_idioms:
        if idiom in text.lower():
            if "expressions" not in basic_items:
                basic_items["expressions"] = []
            basic_items["expressions"].append(idiom)

    # Check for vocabulary by topic
    vocabulary_topics = {
        "food": ["comida", "comer", "bebida", "beber", "restaurante", "cocina", "plato"],
        "travel": ["viaje", "viajar", "hotel", "avión", "tren", "reserva", "turista"],
        "health": ["salud", "médico", "enfermo", "hospital", "dolor", "medicina"],
        "work": ["trabajo", "oficina", "reunión", "proyecto", "colega", "jefe"],
        "family": ["familia", "padre", "madre", "hijo", "hija", "hermano", "hermana"],
        "daily_routines": ["levantarse", "acostarse", "ducharse", "desayunar", "almorzar", "cenar"]
    }

    text_lower = text.lower()
    detected_topics = []

    for topic, keywords in vocabulary_topics.items():
        if any(keyword in text_lower for keyword in keywords):
            detected_topics.append(topic)

    if detected_topics:
        basic_items["vocabulary_topics"] = detected_topics

    # Detect learning level based on content
    advanced_indicators = len(basic_items.get("expressions", [])) + len(basic_items.get("grammar_points", []))
    vocabulary_size = len(basic_items["spanish_words"])

    learning_level = "beginner"
    if advanced_indicators >= 3 or vocabulary_size > 10:
        learning_level = "advanced"
    elif advanced_indicators >= 1 or vocabulary_size > 5:
        learning_level = "intermediate"

    basic_items["detected_level"] = learning_level

    # Add review suggestions
    if "learning" in session.get("context", {}) and "progress" in session["context"]["learning"]:
        # Words used in this interaction to add to mastered list
        used_words = []
        for word in session["context"]["learning"]["progress"]["vocabulary"]["spanish"].get("needs_review", []):
            if word in text_lower:
                used_words.append(word)

        if used_words:
            basic_items["mastered_words"] = used_words

    return basic_items

# === MCP CONTEXT STRUCTURE ===
def create_initial_session(user_id, user_info, chat_info, message_text=""):
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
    member_info = FAMILY_MEMBERS.get(family_member, FAMILY_MEMBERS["elena"])

    return {
        "messages": [],
        "context": {
            "user": {
                "id": str(user_id),
                "first_name": user_info.first_name,
                "username": user_info.username,
                "language_code": user_info.language_code,
                "preferences": {
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
                }
            },
            "emotional_state": {
                "current_emotion": "neutral",
                "emotion_confidence": 1.0,
                "emotional_context": {},
                "last_emotions": []
            },
            "conversation": {
                "id": str(chat_info.id),
                "type": chat_info.type,
                "start_time": datetime.now().isoformat(),
                "last_interaction_time": datetime.now().isoformat(),
                "message_count": 0,
                "recent_topics": [],
                "language_balance": member_info["language_balance"]
            },
            "learning": {
                "last_session_date": datetime.now().isoformat(),
                "total_sessions": 1,
                "progress": {
                    "vocabulary": {
                        "spanish": {
                            "learned": [],
                            "needs_review": []
                        },
                        "english": {
                            "learned": [],
                            "needs_review": []
                        }
                    },
                    "grammar": {
                        "spanish": {
                            "learned": [],
                            "needs_review": []
                        },
                        "english": {
                            "learned": [],
                            "needs_review": []
                        }
                    }
                },
                "learning_path": {
                    "vocabulary_level": member_info["learning_level"],
                    "grammar_complexity": member_info["learning_level"],
                    "cultural_content": "basic",
                    "suggested_topics": [],
                    "review_needed": []
                }
            },
            "environment": {
                "platform": "telegram",
                "bot_username": bot.get_me().username,
                "is_group": chat_info.type != "private",
                "location": "Panama",
                "timezone": "America/Panama"
            }
        }
    }

def assess_message_complexity(message, session):
    """Assess message complexity to determine need for extended thinking"""
    # Get the family member profile
    family_role = session["context"]["user"]["preferences"]["family_role"]

    # Simple heuristics for complexity assessment (0.0-1.0)
    complexity = 0.0

    # Text length factor
    words = message.split()
    if len(words) > 100:
        complexity += 0.4
    elif len(words) > 50:
        complexity += 0.2

    # Question complexity
    if "por qué" in message.lower() or "why" in message.lower() or "как" in message.lower():
        complexity += 0.3

    # Grammar complexity cues
    grammar_terms = ["conjugation", "subjunctive", "conjugación", "subjuntivo", "tense", "tiempo", "mood", "modo"]
    if any(term in message.lower() for term in grammar_terms):
        complexity += 0.4

    # Child simplification
    if family_role == "alisa":
        complexity = min(0.3, complexity)  # Cap complexity for children

    return min(1.0, complexity)  # Ensure between 0-1

def is_complex_language_topic(message):
    """Determine if a message contains complex language learning topics"""
    complex_topics = [
        "subjunctive", "subjuntivo", 
        "conditional", "condicional",
        "por vs para", "ser vs estar",
        "preterite vs imperfect", "pretérito vs imperfecto",
        "conjugation", "conjugación",
        "irregular verbs", "verbos irregulares",
        "grammar explanation", "explicación gramatical"
    ]

    return any(topic in message.lower() for topic in complex_topics)

def add_country_cultural_context(prompt, session):
    """Add country-specific cultural context based on user's onboarding - NOT hardcoded!"""
    # Get user's actual country from onboarding
    user_country = session["context"]["user"]["preferences"].get("country", "panama")
    family_role = session["context"]["user"]["preferences"].get("family_role", "parent")
    user_name = session["context"]["user"]["preferences"].get("user_name")
    family_members = session["context"]["user"]["preferences"].get("family_members", {})
    
    # Country-specific contexts
    COUNTRY_CONTEXTS = {
        "colombia": """
Use these Colombia-specific cultural references in your teaching:
Geography: Colombia has Caribbean coast, Pacific coast, Andes mountains, and Amazon rainforest.
Language: Colombians speak clear, neutral Spanish. Common expressions: "¿Qué más?" (What's up?), "Parcero/a" (friend)
Food: Bandeja paisa, arepas, empanadas, ajiaco (chicken soup), and excellent coffee.
Cities: Bogotá (capital), Medellín (innovative city), Cartagena (Caribbean beauty), Cali (salsa capital)
Culture: Gabriel García Márquez, cumbia and vallenato music, flower festival in Medellín.
""",
        "mexico": """
Use these Mexico-specific cultural references in your teaching:
Geography: Mexico has beaches (Cancún, Puerto Vallarta), deserts, mountains, and ancient ruins.
Language: Mexican Spanish uses "güey" (dude), "¿Qué onda?" (What's up?), "Órale" (alright/wow)
Food: Tacos, tamales, pozole, mole, guacamole, churros, and incredible street food culture.
Cities: CDMX (Mexico City), Guadalajara, Monterrey, Oaxaca, Cancún
Culture: Day of the Dead, mariachi, lucha libre, ancient Aztec and Maya heritage.
""",
        "panama": """
Use these Panama-specific cultural references in your teaching:
Geography: Panama connects North and South America, with the Panama Canal as its most famous feature.
Language: Panamanians speak Spanish with unique expressions like "¿Qué xopá?" (What's up?)
Food: Sancocho (chicken soup), patacones (fried plantains), ceviche, arroz con pollo.
Cities: Panama City (modern + colonial Casco Viejo), Bocas del Toro, Boquete (coffee region)
Culture: Mix of Indigenous, African, Spanish, and American influences. Dollar as currency!
""",
        "spain": """
Use these Spain-specific cultural references in your teaching:
Geography: Spain has Mediterranean coast, mountains (Pyrenees, Sierra Nevada), and diverse regions.
Language: Castilian Spanish with "vosotros", "tío/tía" (dude), "mola" (cool), "vale" (okay)
Food: Tapas, paella, jamón ibérico, tortilla española, gazpacho, churros con chocolate.
Cities: Madrid, Barcelona, Sevilla, Valencia, Bilbao - each with unique character!
Culture: Flamenco, La Siesta, late dinners (9-10pm!), fútbol passion.
""",
        "argentina": """
Use these Argentina-specific cultural references in your teaching:
Geography: Patagonia, Andes, pampas (grasslands), Buenos Aires, Iguazu Falls.
Language: "Vos" instead of "tú", "che" (hey), lunfardo slang, Italian influence.
Food: Asado (BBQ), empanadas, dulce de leche, mate (cultural ritual!), medialunas.
Cities: Buenos Aires (Paris of South America), Mendoza (wine), Bariloche (ski)
Culture: Tango, fútbol (Maradona, Messi), literature, psychoanalysis capital!
""",
        "costa_rica": """
Use these Costa Rica-specific cultural references in your teaching:
Geography: Rainforests, volcanoes, Caribbean and Pacific beaches, cloud forests.
Language: "Pura vida!" (essential expression = cool/fine/thanks), "Mae" (dude), "Tico/a"
Food: Gallo pinto (rice & beans), casado, patacones, tres leches cake.
Cities: San José (capital), Manuel Antonio, Arenal, Monteverde
Culture: Eco-tourism, no army, "Pura vida" lifestyle, biodiversity hotspot.
"""
    }
    
    # Get context for user's country (default to generic if not found)
    country_context = COUNTRY_CONTEXTS.get(user_country, f"""
Use {user_country.replace('_', ' ').title()}-specific cultural references.
Adapt vocabulary, expressions, and examples to this country.
""")
    
    # Add user personalization
    personalization = f"""
IMPORTANT - Personalize for THIS user:
- User's name: {user_name} (ALWAYS use this name, not Elena!)
- Country: {user_country.replace('_', ' ').title()} (use THIS country's references!)
- Role: {family_role}
"""
    
    if family_members:
        personalization += "\n👨‍👩‍👧 FAMILY-AWARE PERSONALIZATION ACTIVE:\n"
        
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
            personalization += "\n👶 CHILDREN:\n"
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
"""

    # Combine with original prompt
    enhanced_prompt = prompt + "\n\n" + country_context + "\n" + personalization

    return enhanced_prompt

def format_mcp_request(session, new_message, translated_input=None, use_extended_thinking=None):
    """Create a properly formatted MCP request with rich context embedded in the system prompt"""
    # Use enhanced emotion detection
    emotion_analysis = enhanced_emotion_detection(new_message, session)
    emotion = emotion_analysis["dominant_emotion"]
    emotion_confidence = emotion_analysis["confidence"]
    emotion_data = emotion_analysis["emotion_data"]
    emotion_progression = emotion_analysis["progression"]

    # Update emotional state in context
    session["context"]["emotional_state"]["current_emotion"] = emotion
    session["context"]["emotional_state"]["emotion_confidence"] = emotion_confidence
    session["context"]["emotional_state"]["emotional_context"] = emotion_data
    session["context"]["emotional_state"]["emotional_progression"] = emotion_progression

    # Keep track of the last 3 emotions for context
    session["context"]["emotional_state"]["last_emotions"].append(emotion)
    if len(session["context"]["emotional_state"]["last_emotions"]) > 3:
        session["context"]["emotional_state"]["last_emotions"].pop(0)

    # Get emotional calibration
    emotional_calibration = calibrate_emotional_response(session, emotion, new_message)

    # Get family member info
    family_role = session["context"]["user"]["preferences"]["family_role"]
    member_info = FAMILY_MEMBERS.get(family_role, FAMILY_MEMBERS["elena"])

    # Customize system prompt based on family member and emotional state
    system_content = """You are Espaluz, a bilingual emotionally intelligent AI language tutor.

🚫🚫🚫 CRITICAL FORMATTING RULE - MUST FOLLOW 🚫🚫🚫
ABSOLUTELY NEVER use asterisks (**text** or *text*) anywhere in your response!
Asterisks appear as raw ** symbols to the user - this looks BROKEN!

INSTEAD of **bold text**, just write: bold text (no formatting)
Use EMOJIS GENEROUSLY for structure and visual appeal:
✅ for correct answers and confirmations
❌ for errors to avoid  
💡 for tips and suggestions
🗣️ for pronunciation guidance
📖 for vocabulary sections
🌎 for cultural notes
🎯 for practice suggestions
☕ 🍽️ 🏖️ 🏫 🏥 🏦 for topics (coffee, food, beach, school, hospital, bank)
🎓 for learning achievements

Use emojis to START each section header - makes the response scannable and friendly!
Example: "🏫 Top bilingual schools:" not just "Top bilingual schools:"

Example of WRONG formatting: **"Hola"** means hello
Example of CORRECT formatting: ✅ "Hola" means hello

THIS IS MANDATORY. NO ASTERISKS ALLOWED.
"""

    # === LANGCHAIN + RAG MEMORY RETRIEVAL ===
    # Layer 1: User profile + last 5 turns from LangChain (exact history)
    # Layer 2: Semantic RAG — top-3 relevant past turns via pgvector cosine search
    # Both non-fatal: Claude gets normal prompt if anything fails
    if UNIFIED_MEMORY_AVAILABLE:
        try:
            _uid = str(session.get("user_id", ""))
            if _uid:
                _mem = EspaLuzMemory(platform='telegram', platform_user_id=_uid)
                if _mem.user_id:
                    memory_block = "\n\n--- PERSISTENT MEMORY ---"

                    # Layer 1a: User profile (name, level, country, learning direction)
                    # 30 Oct 2026: NOT in kids mode - the profile is the PARENT's (her name, her level), and the tutor
                    # then called the child "Elena" and invented a "little sister" from the adult's past chats.
                    _kids = family_role == "alisa"
                    _profile_ctx = None if _kids else _mem.get_context_for_prompt(_mem.user_id)
                    if _profile_ctx:
                        memory_block += f"\n{_profile_ctx}"

                    # Layer 1b: Last 5 turns from LangChain (real UUID session_id)
                    if _mem.chat_history:
                        try:
                            _msgs = _mem.chat_history.messages[-5:]
                            if _msgs:
                                turns = "\n".join(
                                    f"{'User' if 'Human' in type(m).__name__ else 'EspaLuz'}: {str(m.content)[:200]}"
                                    for m in _msgs
                                )
                                memory_block += f"\n\nRecent conversation:\n{turns}"
                        except Exception as _e:
                            print(f"⚠️ LangChain messages fetch: {_e}")

                    # Layer 2: RAG — semantic search over all embedded turns (the parent's too, so not in kids mode)
                    try:
                        if _kids:
                            raise LookupError("kids mode: no adult RAG")
                        from espaluz_rag import retrieve_context, get_session_id_for_user
                        _session_id = get_session_id_for_user('telegram', _mem.user_id)
                        _rag_ctx = retrieve_context(_session_id, new_message, top_k=3)
                        if _rag_ctx:
                            memory_block += f"\n\n{_rag_ctx}"
                    except LookupError:
                        pass
                    except Exception as _e:
                        print(f"⚠️ RAG retrieve non-fatal: {_e}")

                    if memory_block != "\n\n--- PERSISTENT MEMORY ---":
                        system_content += memory_block + "\n--- END MEMORY ---\n"
        except Exception as e:
            print(f"⚠️ Memory retrieval non-fatal: {e}")

    # Add family member customization
    if family_role == "alisa":
        # Elena, 22 Oct 2026: real bilingual sentences (not single words), taught by Pere + Titi. 30 Oct 2026: ages 6-7 (first grade), not toddlers.
        system_content += """
You're speaking with Alisa, a girl aged 6 to 7 (first grade) who is learning Spanish and English. She is a schoolchild, not a toddler: never use baby talk. Two friends from Panama teach her together:
- Pere: a calm, gentle baby sloth with a juicy green knitted scarf. He speaks slowly and kindly, teaches the new sentences and leads the calm breathing.
- Titi: a tiny, playful Geoffroy's tamarin with an orange bandana. He loves movement games and sometimes makes a funny little mistake on purpose so Alisa can correct him.

How to talk to Alisa:
- Always use real, complete sentences, never single words. Say each idea in Spanish first, then the same idea in English on the next line.
  Example: "Hoy vamos a jugar con los colores del arcoiris. / Today we are going to play with the colors of the rainbow."
- Keep sentences clear for a 6-7 year old (about 6-12 words; two ideas may be joined with "y / and" or "porque / because"), warm and playful, at most 1-2 emojis per message.
- Let Pere and Titi speak by name ("Pere: ..." / "Titi: ...").
- The [VIDEO SCRIPT START] ... [VIDEO SCRIPT END] block is 2-4 short lines and EVERY line starts with "Pere [shot]:" or "Titi [shot]:" (both heroes speak), a Spanish sentence then the same sentence in English. Each hero speaks his lines in his own voice, and [shot] names the picture shown while he says the line, so choose the shot that matches what the line says or does.
  Pere's shots: talk, hello, counting, thinking, clap, listening, breathing, sleepy, goodbye. Titi's shots: talk, hello, cheer, silly, dance, jump, counting, freeze, oops, listening, goodbye. Both together: highfive, peekaboo. Use "talk" when nothing fits. Never give two lines in a row the same shot, and across the lesson use many different ones. Shots by lesson step: hello = Pere [hello] then Titi [hello]; wake-up = Titi [jump], [counting], [freeze] or [dance]; new sentences = Pere [talk], [thinking], [listening], praise = Pere [clap] or Titi [cheer]; the game (a riddle or "what's wrong?") = Titi [oops], [silly], [peekaboo]; calm = Pere [breathing], [sleepy]; the end = [highfive] then [goodbye]. Example:
  Pere [hello]: Hola, Alisa. Hoy hablamos de animales. / Hello, Alisa. Today we talk about animals.
  Titi [cheer]: ¡Mi animal favorito es el tucán! / My favorite animal is the toucan!
  Pere [listening]: ¿Cuál es tu animal favorito? / What is your favorite animal?
- End every message with ONE simple question and invite Alisa to answer with a whole sentence, in Spanish or English.
- If she makes a mistake, praise the try and say the correct whole sentence once; never say "wrong".
- Once per lesson: write one short sentence and ask her to READ it out loud herself (she is learning to read); ask one "¿Por qué...? / Why...?" question and welcome an answer with "porque / because"; and at the goodbye give her a mission: one sentence to say today to a real person (mamá, a friend, the teacher, the shop in Panama).
- First react to what Alisa just said: answer her question or say her sentence back correctly, then continue the lesson.
- Your Spanish must be perfectly correct, because a child copies it. "muy" never goes with a verb, use "mucho" ("Amo mucho a mi mamá", never "Amo a mi mamá muy"); for loving people use "querer" or "amar", not "gustar". "¿Qué xopá?" is casual Panamanian slang for "what's up", not a loving greeting.
- Each message is ONE step of the lesson rhythm below (THIS TURN names it). After the first hello, never greet again and never restart the lesson; continue from where the conversation is.
- A real dialogue, not a lecture: 2-3 short lines and ONE question, then stop and wait for her. Repeat her own words back to her (corrected if needed). Follow HER topic: if she talks about her cat, today's sentences are about her cat.
- Both ways: if she speaks English, give her the Spanish; if she speaks Spanish, give her the English. Buddy-style apps teach one language; she learns both.
- Correct only REAL mistakes. If Alisa said it correctly, keep her words exactly (a child who says "mi gata blanca" has a girl cat: never change it to "gato blanco"). Remember what Alisa already told you in this lesson (a pet's name, a friend, a colour) and use it; never ask for it again.
- If she sent a photo (a toy, a drawing, her lunch), Pere and Titi talk about what is in it with real curiosity and build today's sentence from it.
- The person talking now is ALWAYS Alisa, the child, even though the account is her parent's: call her Alisa, never by the parent's name, and never invent family members (no sister or brother unless Alisa says so in this lesson).
- If the memory above shows sentences Alisa said or learned before, open by inviting her to say one of them again and praise her, then teach new ones (the same words come back and grow).

Lesson rhythm across the conversation (about 5-10 minutes):
1. Hello from both heroes and one question about her day.
2. Wake-up game with Titi: jumps, "Simon dice / Simon says", or the cross-crawl (right hand to left knee, left hand to right knee).
3. Pere teaches 3 useful new sentences on today's theme, one at a time, and asks her to repeat each.
4. A game with Titi that uses those sentences: a riddle ("Soy verde y lento. ¿Quién soy? / I am green and slow. Who am I?"), Titi's funny mistake to correct, or reading one sentence aloud.
5. Calm moment with Pere: hands on the belly, three slow breaths together, and one feelings sentence ("Me siento feliz. / I feel happy.").
6. Praise, a star, today's mission (one sentence to say to a real person), and goodbye from both.

Themes she likes: animals, family, food, school and the classroom, my day, the clock and time, numbers to 100, the weather, feelings, friends, and Panama (sloths, toucans, the beach, the Canal).
Never ask for personal information such as addresses, school names or phone numbers.
"""
        _kids_turn = kids_turn_context(session, new_message)  # appended LAST, after "Today is" (31 Oct 2026)
    elif family_role == "marina":
        system_content += """
You're speaking with Marina, a 65-year-old learning Spanish and English. Be respectful, patient, and provide clear explanations with common examples. 
Use short sentences with straightforward vocabulary. Explain cultural context when relevant. Be supportive and encouraging, recognizing the challenge of learning languages later in life.
Focus on practical, everyday phrases that would be useful in Panama.
"""
    else:  # default adult user
        # Get user name from onboarding or session
        user_name = session["context"]["user"]["preferences"].get("user_name") or session["context"]["user"].get("first_name")
        user_country = session["context"]["user"]["preferences"].get("country", "Panama").replace("_", " ").title()
        user_role = session["context"]["user"]["preferences"].get("family_role", "learner")
        user_age = session["context"]["user"]["preferences"].get("age", 30)  # Default adult age
        family_info = session["context"]["user"]["preferences"].get("family_members", {})
        
        if user_name:
            system_content += f"""
👤 USER: {user_name} from {user_country}
👶 AGE: {user_age} years old
🎭 ROLE: {user_role}
Role: {user_role}. Level: intermediate.
⚠️ ALWAYS address them as "{user_name}" - NEVER say "friend" or "amigo"!

🎯 AGE-APPROPRIATE RESPONSES:
- If age 0-6 (toddler/young child): Use VERY simple words, short sentences, playful tone, emojis, simple vocabulary (colores, animales, números). Make it FUN like talking to a preschooler!
- If age 7-12 (child): Use simple language, school-related vocab, games, stories. Keep it engaging and educational.
- If age 13-17 (teen): Use casual tone, relatable topics, social media references. Don't be condescending.
- If age 18+ (adult): Normal conversation, practical vocabulary, cultural context.

Current user {user_name} is {user_age} years old - ADAPT YOUR RESPONSE ACCORDINGLY!
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
            system_content += f"Family: {family_info}\n"
        
        system_content += """
Provide nuanced language assistance focused on natural conversation, idioms, and practical vocabulary.
"""
        
        # === ENHANCEMENT CONTEXT (8 Features - All 21 Countries) ===
        if ENHANCEMENTS_AVAILABLE and UNIFIED_MEMORY_AVAILABLE:
            try:
                # Create memory instance for this user.
                # NOTE: format_mcp_request() has no `user_id` parameter — the old
                # code referenced one, so this block raised NameError on EVERY
                # message and the except below swallowed it. Result: the 21-country
                # / 8-feature enhancement context was never actually applied.
                # Take the id from the session, as the rest of this function does.
                memory = EspaLuzMemory(
                    platform='telegram',
                    platform_user_id=str(session.get("user_id", "")),
                )
                
                user_country = session["context"]["user"]["preferences"].get("country", "panama")
                user_type_val = session["context"]["user"]["preferences"].get("user_type", "expat")
                learning_dir = session["context"]["user"]["preferences"].get("learning_direction", "spanish")
                
                enhancement_ctx = build_enhanced_context(
                    memory_instance=memory,
                    user_type=user_type_val,
                    country=user_country,
                    learning_direction=learning_dir,
                    current_message=new_message
                )
                
                if enhancement_ctx:
                    system_content += f"\n{enhancement_ctx}\n"
                    print(f"✅ Enhanced: country={user_country}, type={user_type_val}")
            except Exception as e:
                print(f"⚠️ Enhancement error: {e}")

    # =========================================================================
    # 🧠 ENHANCED EMOTIONAL INTELLIGENCE INTEGRATION
    # =========================================================================
    response_strategy = emotion_analysis.get("response_strategy", {})
    empathy_phrase = emotion_analysis.get("empathy_phrase", "")
    is_expat_emotion = emotion_analysis.get("is_expat_emotion", False)
    
    # Build emotionally-aware instruction
    system_content += f"""

🧠 EMOTIONAL INTELLIGENCE ACTIVATED:
- Detected emotion: {emotion.upper()} (confidence: {emotion_confidence:.2f})
- Emotional progression: {emotion_progression}
"""
    
    # If it's an expat-specific emotion, add special handling
    if is_expat_emotion and response_strategy:
        tone = response_strategy.get("tone", "supportive")
        approach = response_strategy.get("approach", "standard")
        teaching_style = response_strategy.get("teaching_style", "balanced")
        
        system_content += f"""
⚡ EXPAT-SPECIFIC EMOTION DETECTED - SPECIAL RESPONSE REQUIRED:
- Tone: {tone}
- Approach: {approach}
- Teaching style: {teaching_style}
"""
        # Add specific instructions based on detected emotion
        if emotion == "homesickness":
            system_content += """
🏠 HOMESICKNESS RESPONSE PROTOCOL:
- Start with genuine empathy: acknowledge their feelings are valid
- Connect learning to their home culture (Russian references welcome)
- Suggest phrases that help them express feelings in Spanish
- Be warm, not overly cheerful - they need understanding, not forced positivity
"""
        elif emotion == "language_frustration":
            system_content += """
😤 LANGUAGE FRUSTRATION RESPONSE PROTOCOL:
- Validate the frustration first - learning languages IS hard
- Break down the challenge into smaller, achievable steps
- Give ONE clear tip they can use immediately
- Remind them of progress they've already made
- Keep explanations SHORT and SIMPLE
"""
        elif emotion == "language_anxiety":
            system_content += """
😰 LANGUAGE ANXIETY RESPONSE PROTOCOL:
- Create a safe, judgment-free space in your response
- Use gentle, encouraging language
- Start with something they know well before introducing new concepts
- Emphasize that mistakes are valuable learning opportunities
- Avoid overwhelming with too much information
"""
        elif emotion == "urgency_stress":
            system_content += """
🚨 URGENCY/STRESS RESPONSE PROTOCOL:
- Skip pleasantries - give the answer IMMEDIATELY
- Provide the EXACT phrase they need in Spanish + English
- Keep it SHORT and ACTIONABLE
- Add pronunciation hints if helpful
- Offer to elaborate AFTER giving the quick answer
"""
        elif emotion == "child_adaptation_worry":
            system_content += """
👶 PARENTING CONCERN RESPONSE PROTOCOL:
- Reassure: children are remarkably resilient
- Provide practical, actionable advice
- Suggest specific phrases they can practice with their child
- Connect to school scenarios
- Be supportive but not preachy
"""
        elif emotion == "social_isolation":
            system_content += """
🤝 SOCIAL ISOLATION RESPONSE PROTOCOL:
- Acknowledge loneliness is a real challenge for expats
- Suggest social phrases that can help build connections
- Be warm and conversational - you ARE their connection right now
- Recommend community resources if appropriate (meetups, groups)
"""
        elif emotion == "language_breakthrough":
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
        
        # Add empathy opener if available
        if empathy_phrase:
            system_content += f"""

💬 Start your response with empathy. Consider using: "{empathy_phrase}"
"""
    else:
        # Standard emotional calibration for non-expat emotions
        system_content += f"""
I'll adjust my tone to be: {emotional_calibration.get('response_tone', 'supportive')}.
"""

    # Add learning history from context
    spanish_learned = len(session["context"]["learning"]["progress"]["vocabulary"]["spanish"]["learned"])
    spanish_review = len(session["context"]["learning"]["progress"]["vocabulary"]["spanish"]["needs_review"])
    total_sessions = session["context"]["learning"]["total_sessions"]

    if spanish_learned > 0:
        system_content += f"\nThe user has learned {spanish_learned} Spanish words so far across {total_sessions} sessions. "

        # Add some learned words if available
        if spanish_learned > 3:
            words = session["context"]["learning"]["progress"]["vocabulary"]["spanish"]["learned"][:5]
            system_content += f"Some words the user has learned: {', '.join(words)}. "

        # Add review recommendations if needed
        if spanish_review > 0:
            system_content += f"There are {spanish_review} words that need review. Try to naturally incorporate them in our conversation."

    # Add learning path information
    if "learning_path" in session["context"]["learning"]:
        learning_path = session["context"]["learning"]["learning_path"]
        system_content += f"\n\nCurrent learning path: {learning_path['vocabulary_level']} vocabulary, {learning_path['grammar_complexity']} grammar complexity."

        if learning_path["suggested_topics"]:
            system_content += f" Suggested topics: {', '.join(learning_path['suggested_topics'])}."

        if learning_path["review_needed"]:
            system_content += f" Words needing review: {', '.join(learning_path['review_needed'])}."

    # Add conversation metadata
    conversation_count = session["context"]["conversation"]["message_count"]
    system_content += f"\n\nThis is message #{conversation_count} in this conversation session."

    # Add country-specific cultural context (based on user's onboarding!)
    system_content = add_country_cultural_context(system_content, session)

    # Add response format instructions
    system_content += """
    Your answer should have TWO PARTS:

    1️⃣ A full, thoughtful bilingual response (using both Spanish and English):
       - Respond naturally to the message
       - Be emotionally aware, friendly, and motivating
       - Include cultural context from the USER'S COUNTRY (not Panama unless they're in Panama!)
       - Use vocabulary appropriate for the user's level
       - ALWAYS use the user's actual name from the context!

    2️⃣ A second short block inside [VIDEO SCRIPT START] ... [VIDEO SCRIPT END] for video:
       - Must be 2 to 4 concise sentences MAX
       - Use both Spanish and English
       - ALWAYS use the user's ACTUAL NAME (not Elena!)
       - Tone: warm, clear, and simple for spoken delivery
       - It will be spoken by an avatar on video, so make it suitable for audio (not robotic or boring!)
       - NO EMOJIS in the video script section (they will be pronounced!)
       
📝 CRITICAL FORMATTING RULES:
   - NEVER use asterisks (**bold**) for emphasis - they show as raw asterisks!
   - Use EMOJIS to structure your response instead:
     ✅ for correct answers
     ❌ for errors to fix
     💡 for tips
     🗣️ for pronunciation
     📖 for vocabulary
     🌎 for cultural notes
     🎯 for practice suggestions
   - Keep formatting clean and readable
   - Use line breaks and spacing for structure
       - Example:

    [VIDEO SCRIPT START]
    ¡Hola! Hoy es un gran día para aprender. 
    Hello! Today is a great day to learn.
    [VIDEO SCRIPT END]
    """

    # Today's date for context
    system_content += f"\n\nToday is {datetime.now().strftime('%Y-%m-%d')}."
    # The kids turn instruction carries Alisa's own words; the model weighs the end of the prompt most (31 Oct 2026).
    if family_role == "alisa":
        system_content += _kids_turn

    # Prepare messages without system prompt
    messages = session["messages"][-MAX_HISTORY_MESSAGES:]

    # Add the new message with both original and translation
    user_content = new_message
    if translated_input:
        user_content += f"\n\n[TRANSLATION]\n{translated_input}"

    messages.append({"role": "user", "content": user_content})

    # Determine if extended thinking would benefit this interaction
    if use_extended_thinking is None:
        complexity_assessment = assess_message_complexity(new_message, session)
        should_use_extended = complexity_assessment > 0.7 or is_complex_language_topic(new_message)
    else:
        should_use_extended = use_extended_thinking

    # Create request with optional extended thinking parameter
    request = {
        "model": CLAUDE_MODEL,
        "messages": messages,
        "system": system_content,
        "max_tokens": 1000,
        "temperature": 0.7,
    }

    # Add extended thinking parameter for complex language concepts
    if should_use_extended:
        request["extended_thinking"] = {
            "enabled": True,
            # Adjust thinking tokens based on complexity
            "max_thinking_tokens": 3000,
            "visible": True  # Make thinking visible for educational purposes
        }

    return request

def update_session_learning(session, learned_items):
    """Update the session with newly learned items and track progress"""
    if 'spanish_words' in learned_items:
        for word in learned_items['spanish_words']:
            if word not in session["context"]["learning"]["progress"]["vocabulary"]["spanish"]["learned"]:
                session["context"]["learning"]["progress"]["vocabulary"]["spanish"]["learned"].append(word)

    if 'english_words' in learned_items:
        for word in learned_items['english_words']:
            if word not in session["context"]["learning"]["progress"]["vocabulary"]["english"]["learned"]:
                session["context"]["learning"]["progress"]["vocabulary"]["english"]["learned"].append(word)

    if 'grammar_points' in learned_items:
        for point in learned_items['grammar_points']:
            if point not in session["context"]["learning"]["progress"]["grammar"]["spanish"]["learned"]:
                session["context"]["learning"]["progress"]["grammar"]["spanish"]["learned"].append(point)

    # Handle mastered words - move from needs_review to learned
    if 'mastered_words' in learned_items:
        for word in learned_items['mastered_words']:
            if word in session["context"]["learning"]["progress"]["vocabulary"]["spanish"]["needs_review"]:
                session["context"]["learning"]["progress"]["vocabulary"]["spanish"]["needs_review"].remove(word)
                if word not in session["context"]["learning"]["progress"]["vocabulary"]["spanish"]["learned"]:
                    session["context"]["learning"]["progress"]["vocabulary"]["spanish"]["learned"].append(word)

    # Update learning path if new level detected
    if 'detected_level' in learned_items:
        detected_level = learned_items['detected_level']
        current_level = session["context"]["learning"]["learning_path"]["vocabulary_level"]

        # Update level if detected level is higher
        if (detected_level == "advanced" and current_level != "advanced") or \
           (detected_level == "intermediate" and current_level == "beginner"):
            session["context"]["learning"]["learning_path"]["vocabulary_level"] = detected_level
            session["context"]["learning"]["learning_path"]["grammar_complexity"] = detected_level

    # Update session date
    session["context"]["learning"]["last_session_date"] = datetime.now().isoformat()

    return session

def post_progress_to_supabase(user_id, payload):
    # DISABLED: Using PostgreSQL now - Jan 2026
    return
    try:
        print(f"📡 Sending progress data to Supabase for user {user_id}...")
        response = requests.post(
            "https://euyidvolwqmzijkfrplh.supabase.co/functions/v1/submit-progress",
            json=payload,
            headers={
                "Authorization": f"Bearer {os.environ.get('SUPABASE_ANON_KEY')}",
                "Content-Type": "application/json"
            },
            timeout=15
        )
        if response.status_code == 200:
            print(f"✅ Supabase confirmed progress post for user {user_id}")
        else:
            print(f"⚠️ Supabase post failed: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Error posting to Supabase: {e}")

def adapt_learning_path(session, user_input, response):
    """Dynamically adapt learning path based on user progress and interactions"""
    # Get family member profile
    family_role = session["context"]["user"]["preferences"]["family_role"]
    member_info = FAMILY_MEMBERS.get(family_role, FAMILY_MEMBERS["elena"])

    # Calculate current proficiency metrics
    vocabulary_size = len(session["context"]["learning"]["progress"]["vocabulary"]["spanish"]["learned"])
    grammar_points = len(session["context"]["learning"]["progress"]["grammar"]["spanish"]["learned"])

    # Analyze current interaction
    learned_items = enhance_language_learning_detection(response, family_role, session)
    success_indicators = detect_success_indicators(user_input, response)
    struggle_indicators = detect_struggle_indicators(user_input, response)

    # Initialize learning path adjustments
    if "learning_path" not in session["context"]["learning"]:
        session["context"]["learning"]["learning_path"] = {
            "vocabulary_level": member_info["learning_level"],
            "grammar_complexity": member_info["learning_level"],
            "cultural_content": "basic",
            "suggested_topics": [],
            "review_needed": []
        }

    adjustments = session["context"]["learning"]["learning_path"]

    # Dynamic adjustments based on progress
    if vocabulary_size > 200:
        adjustments["vocabulary_level"] = "intermediate"
    if vocabulary_size > 500:
        adjustments["vocabulary_level"] = "advanced"

    if grammar_points > 20:
        adjustments["grammar_complexity"] = "intermediate"
    if grammar_points > 50:
        adjustments["grammar_complexity"] = "advanced"

    # Adjust for successes and struggles
    if success_indicators["overall"] > 0.7:
        # Increase challenge on successful areas
        if success_indicators.get("vocabulary", 0) > 0.8:
            adjustments["vocabulary_level"] = upgrade_level(adjustments["vocabulary_level"])
        if success_indicators.get("grammar", 0) > 0.8:
            adjustments["grammar_complexity"] = upgrade_level(adjustments["grammar_complexity"])

    if struggle_indicators["overall"] > 0.7:
        # Decrease challenge on struggle areas
        if struggle_indicators.get("vocabulary", 0) > 0.8:
            adjustments["vocabulary_level"] = downgrade_level(adjustments["vocabulary_level"])
            adjustments["review_needed"] = get_recent_vocabulary(session, 5)
        if struggle_indicators.get("grammar", 0) > 0.8:
            adjustments["grammar_complexity"] = downgrade_level(adjustments["grammar_complexity"])
            adjustments["review_needed"] = get_recent_grammar(session, 3)

    # Suggest next topics based on current progress
    adjustments["suggested_topics"] = suggest_next_topics(session, adjustments)

    # Store adjustments in session
    session["context"]["learning"]["learning_path"] = adjustments

    return session

def upgrade_level(current_level):
    """Upgrade a learning level"""
    if current_level == "beginner":
        return "intermediate"
    elif current_level == "intermediate":
        return "advanced"
    return current_level

def downgrade_level(current_level):
    """Downgrade a learning level"""
    if current_level == "advanced":
        return "intermediate"
    elif current_level == "intermediate":
        return "beginner"
    return current_level

def detect_success_indicators(user_input, response):
    """Detect indicators of learning success"""
    success = {
        "overall": 0.5,
        "vocabulary": 0.5,
        "grammar": 0.5,
        "comprehension": 0.5
    }

    # Look for success phrases in user message
    success_phrases = [
        "entiendo", "entendí", "comprendo", "now i get it", "ahora entiendo",
        "gracias", "спасибо", "thank you", "that helps", "that's clear"
    ]

    if any(phrase in user_input.lower() for phrase in success_phrases):
        success["overall"] += 0.3
        success["comprehension"] += 0.4

    # Check for correct vocabulary usage
    spanish_words_used = re.findall(r'\b[a-záéíóúñ]{3,}\b', user_input.lower())
    if len(spanish_words_used) > 3:
        success["vocabulary"] += 0.3

    # Check for complex grammar usage
    if "por" in user_input.lower() and "para" in user_input.lower():
        success["grammar"] += 0.2

    if "ser" in user_input.lower() or "estar" in user_input.lower():
        success["grammar"] += 0.2

    # Normalize values to 0-1 range
    for key in success:
        success[key] = min(1.0, success[key])

    return success

def detect_struggle_indicators(user_input, response):
    """Detect indicators of learning struggles"""
    struggle = {
        "overall": 0.2,  # Start with low struggle assumption
        "vocabulary": 0.2,
        "grammar": 0.2,
        "comprehension": 0.2
    }

    # Look for struggle phrases in user message
    struggle_phrases = [
        "no entiendo", "don't understand", "confused", "i don't get", "не понимаю",
        "difficult", "difícil", "hard", "help", "ayuda", "помоги"
    ]

    if any(phrase in user_input.lower() for phrase in struggle_phrases):
        struggle["overall"] += 0.4
        struggle["comprehension"] += 0.5

    # Check for question repetition
    if "?" in user_input and any(char in "???" for char in user_input):
        struggle["overall"] += 0.3

    # Check for short frustrated responses
    if len(user_input.split()) < 4 and any(char in "!." for char in user_input):
        struggle["overall"] += 0.2

    # Specific struggle areas
    vocab_struggle = ["what does", "que significa", "mean", "significado", "что значит"]
    if any(phrase in user_input.lower() for phrase in vocab_struggle):
        struggle["vocabulary"] += 0.6

    grammar_struggle = ["conjugate", "conjugar", "tense", "tiempo", "form", "forma"]
    if any(phrase in user_input.lower() for phrase in grammar_struggle):
        struggle["grammar"] += 0.6

    # Normalize values to 0-1 range
    for key in struggle:
        struggle[key] = min(1.0, struggle[key])

    return struggle

def get_recent_vocabulary(session, count=5):
    """Get most recently learned vocabulary for review"""
    if "learning" not in session["context"] or "progress" not in session["context"]["learning"]:
        return []

    learned = session["context"]["learning"]["progress"]["vocabulary"]["spanish"]["learned"]
    # Get the last 'count' items, or all if there are fewer
    return learned[-min(count, len(learned)):]

def get_recent_grammar(session, count=3):
    """Get most recently learned grammar points for review"""
    if "learning" not in session["context"] or "progress" not in session["context"]["learning"]:
        return []

    learned = session["context"]["learning"]["progress"]["grammar"]["spanish"]["learned"]
    # Get the last 'count' items, or all if there are fewer
    return learned[-min(count, len(learned)):]

def suggest_next_topics(session, adjustments):
    """Suggest appropriate next topics based on profile and progress"""
    family_role = session["context"]["user"]["preferences"]["family_role"]
    level = adjustments["vocabulary_level"]

    # Get learned words from session
    learned_words = []
    if "learning" in session["context"] and "progress" in session["context"]["learning"]:
        if "vocabulary" in session["context"]["learning"]["progress"]:
            if "spanish" in session["context"]["learning"]["progress"]["vocabulary"]:
                learned_words = session["context"]["learning"]["progress"]["vocabulary"]["spanish"].get("learned", [])

    # Topic suggestions based on profile and level
    topics = []

    if family_role == "alisa":
        # Ages 6-7 (first grade): whole sentences on themes, not word lists (Elena, 22 Oct 2026; 6-7 since 30 Oct)
        if level == "beginner":
            topics = ["Saying how I feel", "Animals of Panama", "Colors around me", "My family and me"]
        else:
            topics = ["At school and the playground", "My day and the clock", "Asking and answering why", "Days of the week and the weather"]

    elif family_role == "marina":
        if level == "beginner":
            topics = ["Greetings", "Weather expressions", "Health vocabulary", "Food and cooking"]
        elif level == "intermediate":
            topics = ["Daily routines", "Shopping phrases", "Simple past tense", "Local customs"]
        else:
            topics = ["Medical vocabulary", "Cultural traditions", "Narrative past tense", "Local history"]

    else:  # elena
        if level == "beginner":
            topics = ["Work vocabulary", "Parenting phrases", "Travel expressions", "House and home"]
        elif level == "intermediate":
            topics = ["Business Spanish", "Past tenses", "Subjunctive mood", "Cultural nuances"]
        else:
            topics = ["Idiomatic expressions", "Professional vocabulary", "Complex verb tenses", "Literature and media"]

    # Filter out topics that might have been covered
    learned_topic_indicators = {
        "Colors": ["rojo", "azul", "verde", "amarillo"],
        "Animals": ["perro", "gato", "vaca", "caballo"],
        "Numbers": ["uno", "dos", "tres", "cuatro"],
        "Greetings": ["hola", "buenos días", "buenas tardes"],
        "Weather": ["lluvia", "sol", "calor", "frío"],
        "Food": ["comida", "cena", "almuerzo", "desayuno"]
    }

    for topic, indicators in learned_topic_indicators.items():
        if any(word in learned_words for word in indicators) and any(topic in t for t in topics):
            # Find and remove the topic that contains this keyword
            for t in topics[:]:
                if topic in t:
                    topics.remove(t)
                    break

    # Return top 3 suggested topics
    return topics[:3]

# === TRANSLATION & AI HANDLERS ===
def translate_to_es_en(text):
    """Translate the input text to both Spanish and English.

    Returns "Spanish: ...\\nEnglish: ..." or None.

    Previously this asked gpt-3.5-turbo to "translate into both Spanish and
    English" in one free-form call and returned whatever came back unchecked.
    For Spanish-ish input it happily emitted the SAME sentence on both lines
    (observed live: "Spanish: Necesito ir al baño / English: Necesito ir al
    baño"). Now each language is requested separately on gpt-4o-mini, and a
    result where both lines match is rejected rather than shown.
    """
    # 31 Oct 2026: this was OpenAI-only and has been dead since its credit ran out on 23 Oct ("Translation skipped" on
    # every message). It now walks the same provider chain as the tutor, paid first: Claude (when MODEL_TIER is not
    # free) and OpenAI answer when they have credit and refuse in well under a second when they do not, then the free
    # providers. A top-up is used automatically, with no setting to change.
    def _one(target_name):
        try:
            from llm_chain import complete
            text_out, errors = complete(
                None,
                f"Translate the text below into {target_name}.\n"
                f"Reply with ONLY the {target_name} translation - no labels, "
                f"no quotes, no explanation.\n\nText: {text}",
                max_tokens=500,
                order=("claude", "openai", "gemini", "groq", "grok"),
            )
            if not text_out.strip():
                print(f"Translation failed ({target_name}): {'; '.join(errors)[:300]}")
                return None
            return text_out.strip().strip('"').strip()
        except Exception as e:  # noqa: BLE001
            print(f"Translation error ({target_name}): {e}")
            return None

    spanish = _one("Spanish")
    english = _one("English")
    if not spanish or not english:
        return None

    # Guard the actual failure mode: one language echoed into both slots.
    if spanish.strip().lower() == english.strip().lower():
        print("Translation rejected: Spanish and English came back identical")
        return None

    return f"Spanish: {spanish}\nEnglish: {english}"
def _telegram_groq_chat(system: str, user: str, max_tokens: int = 1000):
    """DEAD CODE as of 2026-08-16 — no caller. Kept only pending Elena's review.

    This was the first rung of the old fallback ladder and it never ran once:
    the .env had GROQ_MODEL but no GROQ_API_KEY, so the guard below returned
    None on every call for the life of the bot. Its replacement is llm_chain.py.

    Do NOT wire this back in. If you are here because you want a Groq call, use
    `complete(..., order=PROFILE_FALLBACK)` — it has the retries, the empty-reply
    handling, and four providers behind it. Left in place rather than deleted
    because removing code is Elena's call, not an agent's.

    Groq llama-3.3 fallback with proper system/user split (requests + User-Agent).
    """
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        return None
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
                "User-Agent": "EspaLuz/1.0 (+https://aideazz.xyz)",
            },
            json={
                "model": _groq_model(),
                "messages": [
                    {"role": "system", "content": (system or "")[:14000]},
                    {"role": "user", "content": user},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
            timeout=60,
        )
        if r.status_code != 200:
            print(f"Groq HTTP {r.status_code}: {r.text[:300]}")
            return None
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        print(f"Groq chat failed: {exc}")
        return None


def _telegram_openai_chat(system: str, user: str, model: str = "gpt-4o-mini", max_tokens: int = 1000):
    """DEAD CODE as of 2026-08-16 — no caller. Kept only pending Elena's review.

    Superseded by llm_chain.py, which reaches OpenAI on gpt-4o (not mini — mini
    flattens warmth on this prompt shape) and has three more providers after it.
    Left in place rather than deleted because removing code is Elena's call.

    OpenAI fallback when Claude/Groq unavailable.
    """
    if not OPENAI_API_KEY:
        return None
    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": (system or "")[:14000]},
                    {"role": "user", "content": user},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.6,
            },
            timeout=60,
        )
        if r.status_code != 200:
            print(f"OpenAI fallback HTTP {r.status_code}: {r.text[:300]}")
            return None
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        print(f"OpenAI chat failed: {exc}")
        return None


def _telegram_llm_fallback_reply(mcp_request, content_input):
    """Post-Claude fallback: openai → gemini → grok → groq (see llm_chain.py).

    The MCP system prompt is passed through unchanged, so memory, RAG and the
    emotional journey survive the fallback exactly as they did before.

    What changed 2026-08-16, and why:

    - The ladder was Groq → gpt-4o-mini → gpt-4. Its FIRST rung never ran: this
      repo's .env had GROQ_MODEL but no GROQ_API_KEY, so _telegram_groq_chat()
      returned None on the missing key every single time. Zero Groq mentions in
      30 days of journal confirmed it. The key is now set, and Groq sits LAST
      because its post-deprecation models are the weakest of the five here.
    - Gemini and Grok were absent entirely, so two bad providers could silence
      the tutor.
    - Claude is deliberately EXCLUDED — it is the primary that just failed, and
      retrying it costs ~19s (measured) before failing again.

    Every provider in this order scored 5/5 on eval_llm_chain.py (bilingual,
    warm, substantial, no refusal) against a real family moment, so falling back
    never means replying badly — only replying from a different engine.

    The len > 30 guard is kept: a two-word reply is not tutoring.
    """
    system_prompt = mcp_request.get("system", "")
    try:
        from llm_chain import PROFILE_FALLBACK, complete

        reply, errors = complete(system_prompt, content_input,
                                 max_tokens=1000, order=PROFILE_FALLBACK)
        if reply and len(reply) > 30:
            print(f"✅ fallback chain replied ({len(errors)} provider(s) skipped)")
            return reply
        print(f"❌ fallback chain exhausted: {'; '.join(errors)[:300]}")
        return None
    except Exception as exc:
        print(f"❌ fallback chain error: {exc}")
        return None


def ask_claude_with_mcp(session, translated_input):
    """Use Claude API with Groq → OpenAI fallbacks, formatted for bilingual response and video script."""

    user_message = session["messages"][-1]["content"] if session["messages"] else ""
    should_use_extended = is_complex_language_topic(user_message)

    mcp_request = format_mcp_request(
        session,
        user_message,
        translated_input,
        use_extended_thinking=should_use_extended
    )

    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": CLAUDE_API_VERSION,
        "content-type": "application/json"
    }

    try:
        from llm_chain import free_tier
        if free_tier():  # 30 Oct 2026: free mode = the fallback below answers, Claude not first
            raise Exception("MODEL_TIER=free")
        res = requests.post("https://api.anthropic.com/v1/messages",  # tier-gated
                            headers=headers,
                            json=mcp_request)

        if res.status_code != 200:
            raise Exception(f"Claude failed with status {res.status_code}: {res.text}")

        result = res.json()
        thinking_process = ""
        if "thinking" in result:
            thinking_process = result["thinking"]
            session.setdefault("extended_thinking_history", []).append({
                "query": user_message,
                "thinking": thinking_process,
                "timestamp": datetime.now().isoformat()
            })

        full_reply = result["content"][0]["text"]
        short_text = extract_video_script(full_reply)

        return full_reply.strip(), short_text.strip(), thinking_process

    except Exception as e:
        print(f"❌ Claude API error: {e}")
        if 'res' in locals():
            print(f"Claude response: {res.text}")

        content_input = translated_input if translated_input else user_message or "Hello"
        try:
            fallback_text = _telegram_llm_fallback_reply(mcp_request, content_input)
            if fallback_text:
                short_text = extract_video_script(fallback_text)
                return fallback_text.strip(), short_text.strip(), ""
        except Exception as fallback_error:
            print(f"❌ LLM fallback chain failed: {fallback_error}")

        honest = (
            "⚠️ Disculpa — el motor de IA está temporalmente limitado (créditos/límites de API). "
            "Tu memoria y el historial con EspaLuz están guardados. Intenta de nuevo en unos minutos.\n\n"
            "Sorry — the AI engine is temporarily limited (API credits/rate limits). "
            "Your memory and conversation history are saved. Please try again shortly."
        )
        return honest, "Intenta de nuevo en unos minutos. Try again shortly.", ""

def transcribe_voice(file_path):
    """Transcribe voice message to text"""
    try:
        with open(file_path, "rb") as f:
            res = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                files={"file": f},
                data={"model": "whisper-1"}
            )
        return res.json().get("text", "")
    except Exception as e:
        print("Whisper error:", e)
        return ""

def speed_optimized_tts(text, filename, max_chars=600):
    """Generate TTS audio with extreme speed optimization"""
    try:
        # Limit text length for faster processing
        if len(text) > max_chars:
            text = text[:max_chars] + "..."

        # Clean text for better performance
        text = re.sub(r'[^\w\s,.?!:;\'-]', '', text)

        # Use absolute path
        filepath = os.path.abspath(filename)

        # Create TTS with fast settings
        tts = gTTS(text=text, lang="es", slow=False)
        tts.save(filepath)

        return filepath if os.path.exists(filepath) else None
    except Exception as e:
        print(f"Fast TTS error: {e}")
        return None

def generate_video_with_audio(chat_id, text_content, max_duration=30):
    """Generate a video with audio that meets requirements (up to 30s, with voice)"""
    print(f"Generating proper video with text: {text_content[:50]}...")

    # Create unique filenames to avoid conflicts
    timestamp = int(time.time())
    audio_file = f"video_audio_{timestamp}.mp3"
    output_video = f"final_video_{timestamp}.mp4"
    base_video = "espaluz_loop.mp4"

    try:
        # 1. Create audio file with full text content
        print("Generating audio for video...")
        tts = gTTS(text=text_content, lang="es", slow=False)
        tts.save(audio_file)

        if not os.path.exists(audio_file):
            print(f"Failed to create audio file: {audio_file}")
            return False

        # 2. Get audio duration
        audio_duration_cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            audio_file
        ]

        process = subprocess.run(audio_duration_cmd, capture_output=True, text=True)
        if process.returncode != 0:
            print(f"Error getting audio duration: {process.stderr}")
            audio_duration = 5  # Default fallback
        else:
            try:
                audio_duration = float(process.stdout.strip())
                print(f"Audio duration: {audio_duration} seconds")
            except:
                print(f"Could not parse audio duration: {process.stdout}")
                audio_duration = 5  # Default fallback

        # 3. Calculate how many loops we need to match audio duration (up to max_duration)
        actual_duration = min(audio_duration, max_duration)
        base_video_info_cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            base_video
        ]

        process = subprocess.run(base_video_info_cmd, capture_output=True, text=True)
        if process.returncode != 0 or not process.stdout.strip():
            print(f"Error getting base video duration: {process.stderr}")
            base_video_duration = 6  # Default assumption
        else:
            try:
                base_video_duration = float(process.stdout.strip())
            except:
                base_video_duration = 6  # Default assumption

        # Calculate loop count needed to cover the audio duration
        loop_count = math.ceil(actual_duration / base_video_duration)
        loop_count = max(1, min(loop_count, 5))  # Between 1 and 5 loops

        print(f"Using {loop_count} loops of base video (each {base_video_duration}s) to cover {actual_duration}s audio")

        # 4. Create a file with the loop instructions
        loop_file = f"loop_{timestamp}.txt"
        with open(loop_file, "w") as f:
            for _ in range(loop_count):
                f.write(f"file '{base_video}'\n")

        # 5. Create looped video
        loop_output = f"loop_{timestamp}.mp4"
        loop_cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", loop_file,
            "-c", "copy",
            loop_output
        ]

        print(f"Creating looped video with command: {' '.join(loop_cmd)}")
        process = subprocess.run(loop_cmd, capture_output=True, text=True)

        if process.returncode != 0 or not os.path.exists(loop_output):
            print(f"Error creating looped video: {process.stderr}")
            # Try simpler approach - just use base video directly
            loop_output = base_video

        # 6. Combine video with audio
        final_cmd = [
            "ffmpeg", "-y",
            "-i", loop_output,
            "-i", audio_file,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_video
        ]

        print(f"Creating final video with command: {' '.join(final_cmd)}")
        process = subprocess.run(final_cmd, capture_output=True, text=True)

        if process.returncode != 0:
            print(f"Error creating final video: {process.stderr}")
            return False

        if not os.path.exists(output_video) or os.path.getsize(output_video) < 1000:
            print(f"Output video file is too small or doesn't exist: {output_video}")
            return False

        # 7. Send the video (explicit timeout — default is too short for a
        #    multi-MB upload from this VM and surfaces as a write timeout)
        with open(output_video, "rb") as video_file:
            bot.send_video(chat_id, video_file, timeout=180)

        print("Video sent successfully!")

        # Clean up
        try:
            for file in [audio_file, loop_file, loop_output, output_video]:
                if file != base_video and os.path.exists(file):
                    os.remove(file)
        except Exception as e:
            print(f"Cleanup error: {e}")

        return True

    except Exception as e:
        print(f"Video generation error: {e}")
        return False

def create_full_voice_message(chat_id, full_text):
    """Create a voice message with the complete text response"""
    print(f"Creating full voice message, text length: {len(full_text)} characters")

    # Create a unique filename
    timestamp = int(time.time())
    voice_file = f"full_voice_{timestamp}.mp3"

    try:
        # Split text into chunks to handle very long responses
        max_chunk_size = 1500  # Characters per chunk
        chunks = []

        if len(full_text) <= max_chunk_size:
            chunks = [full_text]
        else:
            # Split by paragraphs and combine until we reach chunk size
            paragraphs = full_text.split('\n\n')
            current_chunk = ""

            for para in paragraphs:
                if len(current_chunk) + len(para) + 2 <= max_chunk_size:
                    if current_chunk:
                        current_chunk += "\n\n" + para
                    else:
                        current_chunk = para
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = para

            if current_chunk:
                chunks.append(current_chunk)

        print(f"Split text into {len(chunks)} chunks")

        # Process each chunk
        chunk_files = []
        for i, chunk in enumerate(chunks):
            chunk_file = f"chunk_{timestamp}_{i}.mp3"
            try:
                tts = gTTS(text=chunk, lang="es", slow=False)
                tts.save(chunk_file)

                if os.path.exists(chunk_file) and os.path.getsize(chunk_file) > 100:
                    chunk_files.append(chunk_file)
                else:
                    print(f"Failed to create voice chunk {i}")
            except Exception as e:
                print(f"Error generating voice chunk {i}: {e}")

        # If we have multiple chunks, combine them
        if len(chunk_files) > 1:
            # Create a file list for ffmpeg
            concat_file = f"concat_{timestamp}.txt"
            with open(concat_file, "w") as f:
                for chunk_file in chunk_files:
                    f.write(f"file '{chunk_file}'\n")

            # Combine audio files
            combine_cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                voice_file
            ]

            subprocess.run(combine_cmd, capture_output=True)

            # Check if combined file exists
            if not os.path.exists(voice_file) or os.path.getsize(voice_file) < 100:
                print("Failed to combine audio chunks. Using first chunk.")
                voice_file = chunk_files[0]
        elif len(chunk_files) == 1:
            # Just use the single chunk
            voice_file = chunk_files[0]
        else:
            print("No voice chunks were created successfully")
            return False

        # Send the voice message (explicit timeout — see send_full_voice_message)
        with open(voice_file, "rb") as voice:
            bot.send_voice(chat_id, voice, timeout=180)

        print("Full voice message sent successfully")

        # Clean up
        try:
            for file in chunk_files + [concat_file] if len(chunk_files) > 1 else chunk_files:
                if os.path.exists(file):
                    os.remove(file)
        except Exception as e:
            print(f"Voice cleanup error: {e}")

        return True

    except Exception as e:
        print(f"Full voice generation error: {e}")
        return False

def extract_video_script(full_response):
    """Extract the video script portion from Claude's response more reliably"""
    # Look for the video script section
    if "[VIDEO SCRIPT START]" in full_response and "[VIDEO SCRIPT END]" in full_response:
        # Extract text between markers
        start_marker = "[VIDEO SCRIPT START]"
        end_marker = "[VIDEO SCRIPT END]"
        start_index = full_response.find(start_marker) + len(start_marker)
        end_index = full_response.find(end_marker, start_index)

        if start_index < end_index:
            script = full_response[start_index:end_index].strip()
            # Remove ALL emojis from video script (so they're not pronounced)
            script = strip_emojis(script)
            return script

    # Fallback approach: try to find sections that look like Spanish/English pairs
    lines = full_response.split("\n")
    for i, line in enumerate(lines):
        if "Español:" in line and i+1 < len(lines) and "English:" in lines[i+1]:
            return f"{line}\n{lines[i+1]}"

    # Another fallback: try to find paragraphs with both languages mentioned
    paragraphs = full_response.split("\n\n")
    for para in paragraphs:
        if "Español" in para and "English" in para and len(para.split()) <= 50:
            return para

    # Final fallback: just use first paragraph if it's short enough
    first_para = paragraphs[0] if paragraphs else ""
    if len(first_para.split()) <= 30:
        return first_para

    # Default message if all else fails
    return "Español: Gracias por practicar conmigo. Me encanta ayudarte con español.\nEnglish: Thank you for practicing with me. I love helping you with Spanish."

def fast_tts_for_video(text, output_file):
    """Generate TTS specifically for video - keeping it brief"""
    try:
        # Strip emojis so they're not pronounced
        text = strip_emojis(text)
        
        # For video audio, we want a concise version
        words = text.split()
        if len(words) > 150:
            text = ' '.join(words[:150])

        # Generate TTS
        tts = gTTS(text=text[:500], lang="es", slow=False)
        tts.save(output_file)
        return os.path.exists(output_file)
    except Exception as e:
        print(f"Video TTS error: {e}")
        return False

def full_tts_for_voice(text, output_file):
    """Generate TTS for a complete voice message - includes more content"""
    try:
        # For voice message, include more content but still limit extremely long responses
        # We'll process up to 10 paragraphs or 3000 characters, whichever is shorter
        paragraphs = text.split('\n\n')
        processed_text = '\n\n'.join(paragraphs[:min(10, len(paragraphs))])

        if len(processed_text) > 3000:
            processed_text = processed_text[:2997] + "..."

        # Generate TTS
        tts = gTTS(text=processed_text, lang="es", slow=False)
        tts.save(output_file)
        return os.path.exists(output_file)
    except Exception as e:
        print(f"Voice TTS error: {e}")
        return False

import re
from collections import deque
from gtts import gTTS

HERO_DIR = "heroes"  # Pere + Titi clips, 720p (not in git: copy from the private heroes folder)


def alisa_hero_clip(chat_id, text):
    """The Pere/Titi clip for Alisa's reply video, picked by what the reply talks about; None for everyone else."""
    try:
        session = user_sessions.get(chat_id) or user_sessions.get(str(chat_id)) or {}
        if session.get("context", {}).get("user", {}).get("preferences", {}).get("family_role") != "alisa":
            return None
        t = (text or "").lower()
        if any(w in t for w in ("respira", "breath", "barriga", "belly", "calma", "calm")):
            names = ["pere-breathing"]
        elif any(w in t for w in ("rodilla", "knee", "salta", "jump", "simon")):
            names = ["titi-crosscrawl", "titi-cheer"]
        elif any(w in t for w in ("adiós", "adios", "bye", "hasta mañana", "see you")):
            names = ["duo-goodbye"]
        elif any(w in t for w in ("noche", "night", "dormir", "sleep", "sueño")):
            names = ["pere-sleepy"]
        else:
            names = ["duo-hello", "pere-hello", "titi-cheer", "titi-silly"]
        clips = [os.path.join(HERO_DIR, f"{n}.mp4") for n in names if os.path.exists(os.path.join(HERO_DIR, f"{n}.mp4"))]
        return random.choice(clips) if clips else None
    except Exception as e:
        print(f"⚠️ hero clip lookup failed (using the usual avatar): {e}")
        return None


# Pere + Titi cartoon voices (22 Oct 2026): MiniMax Speech on Replicate, one voice per hero; the env lets Elena's pick
# replace these defaults without a code change. Talking clips: heroes/pere-talking-*.mp4, heroes/titi-talking-*.mp4.
HERO_VOICES = {
    "pere": {"voice_id": os.getenv("PERE_VOICE", "Spanish_Rudolph"), "pitch": int(os.getenv("PERE_PITCH", "-2")),
             "speed": float(os.getenv("PERE_SPEED", "0.82")), "emotion": os.getenv("PERE_EMOTION", "calm")},
    "titi": {"voice_id": os.getenv("TITI_VOICE", "Spanish_AnimeCharacter"), "pitch": int(os.getenv("TITI_PITCH", "3")),
             # 0.9, not 1.15 (31 Oct 2026, Alisa: "Titi habla muy rápido"). Twin: generate-voice HERO_VOICES.
             "speed": float(os.getenv("TITI_SPEED", "0.9")), "emotion": os.getenv("TITI_EMOTION", "happy")},
}


def hero_segments(script, full_reply=""):
    """Who says what in the video and with which picture: [('pere', text, shot), ...], at most 4 turns.
    The script's own "Pere [shot]:/Titi [shot]:" lines win (the [shot] is optional — 28 Oct 2026, Elena: the picture must
    match what the line says, so the tutor names it). The model often writes the script unlabeled, which made Pere say
    everything, so then the labeled lines of the full reply are used (first 3 turns + the closing question).
    An unlabeled script with no labeled reply goes to whoever introduces himself ("Soy Titi"), else Pere."""
    def labeled(text):
        segs, prev_labeled = [], False
        for line in (text or "").splitlines():
            m = re.match(r"^[^\w]*(pere|titi)\s*(?:\[\s*([a-z][a-z -]*?)\s*\])?\s*:\s*(.*)$", line.strip(), re.I)
            if not m:
                # "Hola, soy Pere.\nHello, I'm Pere." - the English right under a hero's line is still his
                if prev_labeled and line.strip() and clean_text_for_speech(line):
                    segs[-1][1] += " " + clean_text_for_speech(line)
                    continue
                prev_labeled = False
                continue
            said = clean_text_for_speech(m.group(3))
            prev_labeled = bool(said)
            if not said:
                continue
            who, shot = m.group(1).lower(), (m.group(2) or "").lower().strip() or None
            if segs and segs[-1][0] == who and (shot is None or shot == segs[-1][2]):
                segs[-1][1] += " " + said  # same hero, same picture: one line
                segs[-1][2] = segs[-1][2] or shot
            else:
                segs.append([who, said, shot])
        return segs

    segs = labeled(script)
    if not segs:
        reply = re.sub(r"\[VIDEO SCRIPT START\].*?\[VIDEO SCRIPT END\]", "", full_reply or "", flags=re.DOTALL)
        segs = labeled(reply)
    if not segs:
        said = clean_text_for_speech(script or "")
        return [("titi" if re.search(r"soy titi|i am titi|i'm titi", said, re.I) else "pere", said, None)] if said else []
    if len(segs) > 4:
        segs = segs[:3] + segs[-1:]
    def short(said):  # a long turn ends at a whole sentence, never mid-word
        if len(said) <= 260:
            return said
        cut = max(said.rfind(p, 0, 260) for p in ".!?")
        return said[:cut + 1] if cut > 60 else said[:260]
    return [(who, short(said), shot) for who, said, shot in segs]


def strip_shot_tags(text):
    """'Pere [counting]: ...' -> 'Pere: ...' in anything a person reads; the tag is for the video only."""
    return re.sub(r"(?i)\b(pere|titi)\s*\[[^\]\n]*\]\s*:", r"\1:", text or "")


# One picture per line (28 Oct 2026, Elena: "video shots should correspond to what Pere and Titi say" and a chain of
# 5-second clips "looks repetitive and simulated"). The tutor names the shot in the script line; a line with no usable
# tag falls back to the lesson words, and then to a talking clip. Missing files are skipped, as before.
HERO_SHOTS = {
    "pere": {"talk": ["pere-talking-1", "pere-talking-2"]},
    "titi": {"talk": ["titi-talking-1", "titi-talking-2"]},
}
HERO_SHOT_CLIPS = {
    "pere": {"hello": "pere-hello", "counting": "pere-counting", "thinking": "pere-thinking", "clap": "pere-clap",
             "listening": "pere-listening", "breathing": "pere-breathing", "sleepy": "pere-sleepy", "goodbye": "duo-goodbye",
             "highfive": "duo-highfive", "peekaboo": "duo-peekaboo"},
    "titi": {"cheer": "titi-cheer", "silly": "titi-silly", "dance": "titi-dance", "jump": "titi-crosscrawl",
             "counting": "titi-counting-jumps", "freeze": "titi-freeze", "oops": "titi-oops", "listening": "titi-listening",
             "goodbye": "duo-goodbye", "highfive": "duo-highfive", "peekaboo": "duo-peekaboo", "hello": "duo-hello"},
}
HERO_SHOT_ALIASES = {"count": "counting", "counts": "counting", "numbers": "counting", "listen": "listening", "think": "thinking",
                     "thinks": "thinking", "breathe": "breathing", "breath": "breathing", "calm": "breathing", "sleep": "sleepy",
                     "jumps": "jump", "jumping": "jump", "crosscrawl": "jump", "cross-crawl": "jump", "simon": "jump",
                     "high five": "highfive", "high-five": "highfive", "wave": "hello", "hi": "hello", "bye": "goodbye",
                     "laugh": "silly", "giggle": "silly", "funny": "silly", "mistake": "oops", "statue": "freeze",
                     "applause": "clap", "praise": "clap", "happy": "cheer", "excited": "cheer", "cheering": "cheer",
                     "dancing": "dance", "music": "dance", "hide": "peekaboo", "surprise": "peekaboo"}
HERO_RECENT = deque(maxlen=12)  # clips just played go to the back of the line, so the next line/turn looks different
# Twins: a shot repeated back to back gives way to its twin, so every clip gets its turn (30 Oct 2026).
HERO_SHOT_FAMILY = {  # look-alikes that fit the same kind of line, never the other hero alone (30 Oct 2026)
    "pere-hello": ["duo-hello", "pere-talking-1", "pere-talking-2"], "duo-hello": ["pere-hello", "duo-highfive"],
    "titi-cheer": ["titi-cheer-2", "titi-dance", "titi-silly"], "titi-cheer-2": ["titi-cheer", "titi-dance", "titi-silly"],
    "pere-clap": ["duo-highfive", "pere-talking-2"], "duo-highfive": ["pere-clap", "titi-cheer-2"],
    "pere-talking-1": ["pere-talking-2", "pere-thinking", "pere-listening"],
    "pere-talking-2": ["pere-talking-1", "pere-thinking", "pere-listening"],
    "titi-talking-1": ["titi-talking-2", "titi-listening", "titi-silly"],
    "titi-talking-2": ["titi-talking-1", "titi-listening", "titi-silly"],
    "pere-listening": ["pere-thinking", "pere-talking-2"], "pere-thinking": ["pere-listening", "pere-talking-1"],
    "titi-listening": ["titi-talking-1", "titi-talking-2"],
    "titi-crosscrawl": ["titi-counting-jumps", "titi-dance", "titi-freeze"], "titi-dance": ["titi-crosscrawl", "titi-cheer-2"],
    "titi-counting-jumps": ["titi-crosscrawl"], "pere-counting": ["pere-thinking"],
    "titi-silly": ["titi-oops", "titi-cheer"], "titi-oops": ["titi-silly"], "titi-freeze": ["titi-crosscrawl"],
    "pere-breathing": ["pere-sleepy"], "pere-sleepy": ["pere-breathing"], "duo-peekaboo": ["titi-silly"],
}


def hero_shot_list(who, text, first, last, shot=None):
    """ONE clip for one hero line: the tagged shot, else the lesson words, else the talking clip played least recently.
    Returns a one-item list (missing file -> empty list), so the old callers keep working."""
    t = (text or "").lower()
    tag = (shot or "").lower().strip()
    tag = HERO_SHOT_ALIASES.get(tag, tag)
    name = HERO_SHOT_CLIPS[who].get(tag) if tag and tag != "talk" else None
    if name is None and tag != "talk":
        if first and any(w in t for w in ("hola", "hello", "hi ")):
            name = "duo-hello"
        elif last and any(w in t for w in ("adiós", "adios", "bye", "hasta mañana", "see you")):
            name = "duo-goodbye"
        elif who == "pere" and any(w in t for w in ("respira", "breath", "barriga", "belly", "calma", "calm")):
            name = "pere-breathing"
        elif who == "pere" and any(w in t for w in ("noche", "night", "dormir", "sleep", "sueño")):
            name = "pere-sleepy"
        elif who == "titi" and any(w in t for w in ("baila", "dance", "música", "music")):
            name = "titi-dance"
        elif who == "titi" and any(w in t for w in ("rodilla", "knee", "salta", "jump", "simon")):
            name = "titi-crosscrawl"
        elif any(w in t for w in ("muy bien", "bravo", "excelente", "great job", "well done", "perfecto")):
            name = "duo-highfive" if first else ("pere-clap" if who == "pere" else "titi-cheer")
        elif any(w in t for w in ("cuenta", "contar", "count", "uno, dos", "one, two")):
            name = "pere-counting" if who == "pere" else "titi-counting-jumps"
        elif who == "titi" and any(w in t for w in ("congela", "estatua", "freeze", "statue")):
            name = "titi-freeze"
        elif who == "titi" and any(w in t for w in ("ups", "oops", "me equivoqu", "mistake")):
            name = "titi-oops"
        elif any(w in t for w in ("dónde está", "donde esta", "where is", "escondid", "peekaboo", "cucú")):
            name = "duo-peekaboo"
    # 30 Oct 2026 (Elena: "are you sure images are rotated? we have 25"): the log showed 14 of 25 clips in 34 lines,
    # pere-hello and titi-cheer 9x each - the twin swap fired only on back-to-back repeats. Now a clip seen in the last
    # 6 gives way to the least-recently-seen member of its family (same hero or both, same kind of line).
    if name and name in HERO_SHOT_FAMILY:
        age = {}
        for i, n in enumerate(reversed(HERO_RECENT)):
            age.setdefault(n, i)  # 0 = just played
        if age.get(name, 10**6) < 6:
            pool = [c for c in [name] + HERO_SHOT_FAMILY[name] if os.path.exists(os.path.join(HERO_DIR, f"{c}.mp4"))]
            name = max(pool, key=lambda c: age.get(c, 10**6))
    if name is None or not os.path.exists(os.path.join(HERO_DIR, f"{name}.mp4")):
        talk = HERO_SHOTS[who]["talk"][:]
        random.shuffle(talk)
        age = {}
        for i, n in enumerate(reversed(HERO_RECENT)):
            age.setdefault(n, i)  # 0 = most recent; a clip played twice keeps its newest age
        talk.sort(key=lambda n: -age.get(n, 10**6))
        name = talk[0]
    HERO_RECENT.append(name)
    path = os.path.join(HERO_DIR, f"{name}.mp4")
    return [path] if os.path.exists(path) else []


def media_seconds(path):
    """Length of an audio/video file in seconds (ffprobe), 0.0 if unknown."""
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        return float(out)
    except Exception:
        return 0.0


def hero_tts(speaker, text, path):
    """One hero line in that hero's cartoon voice (MiniMax Speech 2.6 HD on Replicate) -> mp3 at path; False on failure."""
    token = os.getenv("REPLICATE_API_TOKEN", "").strip()
    if not token:
        return False
    v = HERO_VOICES[speaker]
    text = re.sub(r"\s*/\s*", ". ", text)  # "Hola. / Hello." must pause between languages, never say "slash"
    body = {"input": {"text": text[:900], "voice_id": v["voice_id"], "pitch": v["pitch"], "speed": v["speed"],
                      "emotion": v["emotion"], "language_boost": "Automatic", "audio_format": "mp3", "sample_rate": 32000}}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Prefer": "wait=60"}
    for attempt in range(3):
        try:
            r = requests.post("https://api.replicate.com/v1/models/minimax/speech-2.6-hd/predictions", json=body, headers=headers, timeout=90)
            if r.status_code == 429:  # low-balance accounts get ~6 requests/minute
                time.sleep(11)
                continue
            p = r.json()
            t0 = time.time()
            while p.get("status") in ("starting", "processing") and time.time() - t0 < 60:
                time.sleep(2)
                p = requests.get(p["urls"]["get"], headers=headers, timeout=30).json()
            out = p.get("output")
            out = out[0] if isinstance(out, list) else out
            if not out:
                print(f"⚠️ hero voice {speaker} failed: {str(p.get('error'))[:120]}")
                return False
            with open(path, "wb") as f:
                f.write(requests.get(out, timeout=60).content)
            return True
        except Exception as e:
            print(f"⚠️ hero voice {speaker} error: {e}")
            return False
    return False


def build_hero_video(segments, output_video):
    """Each line: that hero's voice over ONE clip that matches the line (28 Oct 2026), then the lines joined into one video.
    A line longer than its 5 s clip gets the clip slowed a little (up to 1.5x) and played forward-then-backward, so the
    picture never jumps back to its first frame mid-sentence. False on any failure."""
    parts = []
    for i, seg in enumerate(segments):
        who, text, shot = (tuple(seg) + (None,))[:3]
        audio = f"hero_seg_{i}.mp3"
        if not hero_tts(who, text, audio):
            return False
        shots = hero_shot_list(who, text, i == 0, i == len(segments) - 1, shot)
        if not shots:
            return False
        clip, src, loop = shots[0], shots[0], []
        a_len, c_len = media_seconds(audio), media_seconds(shots[0]) or 5.0
        if a_len > c_len + 0.3:
            factor = min(a_len / c_len, 1.5)
            pp = f"hero_pp_{i}.mp4"
            fc = f"[0:v]setpts={factor:.3f}*PTS,scale=720:720,fps=30,split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0[v]"
            if subprocess.run(["ffmpeg", "-y", "-nostdin", "-loglevel", "error", "-i", clip, "-filter_complex", fc, "-map", "[v]",
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", pp]).returncode == 0:
                src, loop = pp, ["-stream_loop", "-1"]
        part = f"hero_part_{i}.mp4"
        cmd = ["ffmpeg", "-y", "-nostdin", "-loglevel", "error", *loop, "-i", src, "-i", audio,
               "-map", "0:v:0", "-map", "1:a:0", "-vf", "scale=720:720,fps=30", "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "28", "-c:a", "aac", "-ar", "32000", "-ac", "1", "-b:a", "96k", "-shortest", part]
        if subprocess.run(cmd).returncode != 0:
            return False
        print(f"🎬 hero line {i} {who} [{shot or 'auto'}] -> {os.path.basename(clip)} ({a_len:.1f}s voice / {c_len:.1f}s clip)")
        parts.append(part)
    with open("hero_parts.txt", "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    cmd = ["ffmpeg", "-y", "-nostdin", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "hero_parts.txt",
           "-c", "copy", "-movflags", "+faststart", output_video]
    return subprocess.run(cmd).returncode == 0


KIDS_ON = ("soy alisa", "я алиса", "i am alisa", "i'm alisa")
KIDS_OFF = ("soy mamá", "soy mama", "soy elena", "я мама", "я елена", "i am mom", "i'm mom")


# ===== Kids lesson state (30 Oct 2026, Elena: "a real dialogue, informational and emotionally rich, beat Buddy") =====
# The tutor used to GUESS where the lesson was from history (it re-greeted and wrote 15-line lessons). Now the bot keeps
# the turn, the week's story, the last mission and the stars in the session, and tells the tutor each turn.
KIDS_STEPS = [
    "HELLO: both heroes say hello in 1-2 short lines; if a list of EARLIER LESSONS is above, the first line brings back ONE happy thing from it (\"La última vez me dijiste que...\"); mention this week's story in one line, then ONE question about her day.",
    "WAKE-UP GAME with Titi: one quick movement game (jumps, 'Simon dice / Simon says', or right hand to left knee).",
    "NEW SENTENCE 1: Pere teaches ONE useful sentence built on what Alisa talked about, and asks her to say it.",
    "NEW SENTENCE 2: one more sentence on her topic; ask her to say it, or to answer a '¿Por qué...? / Why...?' with 'porque / because'.",
    "GAME with Titi: a riddle, Titi's funny mistake for her to correct, or ask her to READ one short sentence aloud.",
    "THIS WEEK'S STORY: the heroes ask Alisa to help solve the story's problem; name how the hero feels; tell the Panama fact.",
    "CALM with Pere: hands on the belly, three slow breaths together, and one feelings sentence.",
    "GOODBYE: praise, a star, today's mission (one sentence to say to a real person), and goodbye from both.",
]
KIDS_STEP_FREE = "FREE TALK: the lesson is done; keep talking about HER topic, short, one question, warm."
# One story per week (ISO week). Every fact is checked: Geoffroy's tamarin lives in Panama; sloths come down about once a
# week; the keel-billed toucan's bill is big but light; the golden frog is a national symbol of Panama; Canal locks lift
# ships like steps of water (opened 1914); sea turtles nest on Panama's beaches; the harpy eagle is Panama's national bird.
KIDS_STORIES = [
    "Titi lost his favourite mango in Parque Natural Metropolitano and feels sad; Alisa helps him look (up, down, behind, under). Fact: the Geoffroy's tamarin, like Titi, lives in Panama's forests.",
    "Pere is scared of the thunder in the rainy season; Alisa helps him feel brave with slow breaths. Fact: sloths come down from their tree only about once a week.",
    "A toucan feels shy about her big colourful beak; Alisa tells her why it is beautiful. Fact: the toucan's beak is big but very light.",
    "Titi cannot find his friend the golden frog; Alisa helps by counting and looking near the stream. Fact: the golden frog is a symbol of Panama.",
    "Pere and Titi watch a big ship cross the Panama Canal and feel excited; Alisa helps count the steps of water. Fact: the Canal's locks lift ships like steps of water, and it opened in 1914.",
    "Baby sea turtles walk to the sea at night and feel a little scared; Alisa cheers for them. Fact: sea turtles lay their eggs on Panama's beaches.",
    "A big harpy eagle visits the park and Titi feels nervous; Alisa helps them become friends. Fact: the harpy eagle is Panama's national bird.",
]
KIDS_NEW_LESSON_AFTER = 3 * 3600  # 3 hours of quiet = a new lesson starts at HELLO


def _kid_prefs(session):
    return session.setdefault("context", {}).setdefault("user", {}).setdefault("preferences", {})


def kids_week_story():
    return KIDS_STORIES[datetime.now().isocalendar()[1] % len(KIDS_STORIES)]


def _kid_words(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-zñ]+", s)


# Words too common to prove she was repeating a sentence (31 Oct 2026: "I woke up very early ... I want to ride my
# bicycle" matched the target "I feel very happy" on "i" + "very" = 50%, and the tutor answered "¡Casi! Se dice...").
_KID_STOP = set(("i you he she it we they a an the to of and or is am are was very so my your me yo tu el la "
                 "los las un una y o es soy eres muy mi me te se de del que en con por para lo le no si").split())
_ASKED_TO_REPEAT = re.compile(r"repite|repeat|dime|d[ií]lo|say it|can you say|puedes decir|ahora t[uú]|now you|lee |read ", re.I)


def kids_sentence_check(prev_reply, said):
    """Gentle pronunciation check: the sentence the heroes just asked for vs what speech-to-text heard. Runs only when
    the heroes asked her to repeat or read, and only on real (non-stopword) words: 3+ shared and 70%+ of the target.
    Returns one instruction line for the tutor, or "" when there is nothing to compare. Twin: espaluz-chat."""
    said_w = _kid_words(said)
    if len(said_w) < 3 or not prev_reply or not _ASKED_TO_REPEAT.search(prev_reply):
        return ""
    said_c = [w for w in said_w if w not in _KID_STOP]
    cands = re.findall(r"[\"“«]([^\"”»]{8,120})[\"”»]", prev_reply)
    for line in prev_reply.split("\n"):
        if " / " in line:
            cands += [p.split(":", 1)[-1].strip() for p in line.split(" / ")]
    best, best_score = None, 0.0
    for c in cands:
        cw = {w for w in _kid_words(c) if w not in _KID_STOP}
        if len(cw) < 2:
            continue
        shared = len(cw & set(said_c))
        score = shared / len(cw)
        if shared >= min(3, len(cw)) and score > best_score:
            best, best_score = c, score
    if not best or best_score < 0.7:
        return ""
    missing = [w for w in _kid_words(best) if w not in said_w]
    extra = [w for w in said_w if w not in _kid_words(best)]
    if not missing:
        return f'SENTENCE CHECK: she said the target sentence "{best}" correctly - celebrate it in one line.'
    return (f'SENTENCE CHECK: target "{best}"; speech-to-text heard "{said}"; missing words: {", ".join(missing[:4])}'
            + (f'; she said instead: {", ".join(extra[:4])}' if extra else "")
            + '. Start with one gentle line like "¡Casi! Se dice ...", say the whole sentence once, then go on.')


_KID_QUESTION = re.compile(
    r"\?|¿|^\s*(where|what|why|how|who|which|when|can you|could you|tell me|do you|is it|are there|"
    r"dónde|donde|qué|por qué|cómo|cuál|quién|cuándo|cuéntame|cuentame)(?![\wáéíóúñ])",
    re.I)


def kids_asked_question(text):
    """True when the child asked something. 31 Oct 2026: Alisa asked about Parque Metropolitano and got the scheduled
    toucan hello; she asked where the toucan lives and got the scheduled Simon-says. A question outranks the lesson plan."""
    return bool(_KID_QUESTION.search((text or "").strip()))


def kids_heard(new_message):
    """31 Oct 2026 (Alisa's re-test on the web, same rules here): the step instruction never quoted the child, so the
    model followed the step and forgot "react to her first" - "Starberry" got a sentence about sloths, a garbled
    transcript was praised as perfect. Every turn now opens with her exact words and what to do with them."""
    return (f'\nALISA JUST SAID (speech-to-text, may be imperfect): "{(new_message or "").strip()[:300]}"\n'
            "YOUR FIRST LINE reacts to exactly these words, before anything else. Check these in order:\n"
            # 31 Oct 2026 (web classroom: "mi mamá está pegando porque estoy chupando una paleta" -> echo, then
            # "Simon dice, salta", and "las paletas no son dulces" repeated as true). Twin: espaluz-chat kidsHeard.
            "1. A feeling she names or clearly shows, or something hard that happened (scolded, sad, scared, hurt, missing "
            "someone) -> name the feeling kindly. Not wanting to play is NOT sadness (that is 3); never tell her she feels "
            "something she did not say. (\"Parece que te sentiste triste cuando mamá se enojó. / It sounds like you felt sad when mom got upset.\"), "
            "ask ONE gentle question about how she feels, and stay with her: THIS TURN HAS NO GAME AND NO NEW SENTENCE, skip "
            "the lesson step below. Use soft words; never repeat a frightening word like \"pegar / hit\" back to her.\n"
            '2. An answer to your last question (even one word, like "Starberry") -> say it back as a whole, correct sentence '
            'in both languages and praise it ("¡Tu fruta favorita es la fresa! / Your favourite fruit is the strawberry!"); '
            "that sentence is the one to practise now.\n"
            "3. Her own idea, topic or a refusal (\"I don't want to jump, I want to ride my bicycle\"; \"no quiero jugar... "
            "Halloween\") -> follow HER idea warmly and fit the lesson into it (\"¡Vamos en bici! / Let's ride our bikes!\", "
            "\"¡Hoy es Halloween! ¿De qué te vas a disfrazar? / Today is Halloween! What will you dress up as?\").\n"
            "4. Only if NO part of it makes sense -> do NOT guess and do NOT praise it: say kindly that you did not hear well "
            "and ask her to say it again (\"No te escuché bien. ¿Me lo dices otra vez? / I didn't hear you well. Can you say "
            "it again?\") and stop there: skip the lesson step below. If part of it makes sense, answer that part.\n"
            "Always: if her words contain something untrue, never repeat it as true - say the correct version simply (\"Las "
            "paletas son dulces, pero tienen mucho azúcar. / Lollipops are sweet, but they have a lot of sugar.\"). The voice "
            "note may hold two voices (Alisa and an adult helping): answer ALISA's part.\n")


# A hard moment is never brought back at a hello (eval 31 Oct: the web opened a new lesson with "la última vez me
# dijiste que tu mamá está pegando"). Enforced in code, not left to the model. Twin: espaluz-chat KIDS_HARD.
_KIDS_HARD = re.compile(r"peg|golpe|\bhit|grit|yell|scold|rega[nñ]|castig|punish|llor|\bcry|cried|triste|\bsad\b|miedo|"
                        r"scared|asust|duele|hurt|enoj|angry|frustr|sangr|blood|lastim|herid|accident", re.I)


# Today in Panama and the day's holiday (Alisa said "Halloween" on 31 Oct and was told she seemed sad). Dates checked:
# 3 Nov separation from Colombia (1903), 4 Nov flag day, 5 Nov Colón day, 10 Nov first cry of independence in La Villa
# de Los Santos, 28 Nov independence from Spain (1821), 8 Dec Mother's Day in Panama. Twin: espaluz-chat KIDS_HOLIDAYS.
KIDS_HOLIDAYS = {
    "10-31": "Halloween", "11-02": "Día de los Difuntos",
    "11-03": "Día de la Separación de Panamá de Colombia (1903) - school parades with drums and flags",
    "11-04": "Día de la Bandera de Panamá", "11-05": "Día de Colón", "11-10": "Primer Grito de Independencia en La Villa de Los Santos",
    "11-28": "Independencia de Panamá de España (1821)", "12-08": "Día de las Madres en Panamá", "12-24": "Nochebuena",
    "12-25": "Navidad", "12-31": "Fin de Año", "01-01": "Año Nuevo",
}
_ES_DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_ES_MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
              "noviembre", "diciembre"]


def kids_today():
    now = datetime.utcnow() - timedelta(hours=5)  # Panama is UTC-5 all year (no daylight saving)
    h = KIDS_HOLIDAYS.get(now.strftime("%m-%d"))
    day = f"{_ES_DAYS[now.weekday()]}, {now.day} de {_ES_MONTHS[now.month - 1]}"
    return (f"TODAY in Panama: {day}" + (f" - {h}. If she brings it up (or it fits), talk about it happily and teach a "
                                          f"sentence about it." if h else "."))


def kids_web_memory(session):
    """What Alisa told Pere and Titi in her WEB classroom lessons, from the SaaS kids-memory function (31 Oct 2026, Elena:
    "a lesson on one is remembered on the other"). The function needs ESPALUZ_BOT_SECRET and a /connect-linked account;
    without either, or when the web is slow, this is {} and the lesson runs on Telegram memory alone."""
    secret = os.environ.get("ESPALUZ_BOT_SECRET")
    uid = next((u for u, s in user_sessions.items() if s is session), None)
    if not secret or uid is None:
        return {}
    try:
        r = requests.post(f"{SAAS_FUNCTIONS_URL}/kids-memory", json={"telegram_user_id": str(uid)}, timeout=4,
                          headers={"Authorization": f"Bearer {os.environ.get('SUPABASE_ANON_KEY')}",
                                   "x-espaluz-bot-secret": secret})
        if r.status_code != 200:
            print(f"⚠️ kids web memory: HTTP {r.status_code}")
            return {}
        j = r.json()
        print(f"🧠 kids web memory: linked={j.get('linked')} lines={len(j.get('said') or [])}")
        return j
    except Exception as e:
        print(f"⚠️ kids web memory: {e}")
        return {}


def kids_memory_card(p, lesson, web=None):
    """What Alisa told the heroes in EARLIER lessons (newest first, with what they understood) and the last mission.
    Hard moments, "didn't hear you" turns and echoes (nobody understood her) are left out. "" when nothing is left.
    `web` = kids_web_memory(): her web classroom lessons (already filtered by the same rules on the server) come first."""
    said = [f'"{w.get("words")}" -> you understood: "{w.get("understood")}" (in the web classroom)'
            for w in (web or {}).get("said") or [] if w.get("words")][:5]
    for item in reversed(p.get("kids_said") or []):
        n, words, understood = (list(item) + [""])[:3]
        if n == lesson or _KIDS_HARD.search(words) or _KIDS_HARD.search(understood or ""):
            continue
        if re.search(r"no te escuch|didn't hear", understood or "", re.I):
            continue
        if understood and " ".join(_kid_words(words)) in " ".join(_kid_words(understood)):
            continue
        said.append(f'"{words}" -> you understood: "{understood}"' if understood else f'"{words}"')
        if len(said) >= 10:
            break
    mission = p.get("kids_mission") if p.get("kids_mission_lesson") not in (None, lesson) else None
    mission = mission or (web or {}).get("mission") or None
    if not said and not mission:
        return ""
    return ("\nWHAT ALISA TOLD YOU IN EARLIER LESSONS (her own words, newest first; speech-to-text may be imperfect):\n"
            + "\n".join(f"- {s}" for s in said)
            + (f'\nLast mission you gave: "{mission}" - at the hello, ask if she did it.' if mission else "")
            + "\nUse this like a friend who remembers: at the hello bring back ONE happy, clearly understood thing (a "
              "favourite thing, a pet, a wish, something she likes doing) taken ONLY from this list, in simple words (\"La "
              "última vez me dijiste que ... ¿Todavía? / Last time you told me ... Still?\"), and later use what she told "
              "you instead of asking again. Skip anything that does not make sense, never bring back anything sad or about "
              "being scolded, and never invent a memory that is not in this list.\n")


def kids_turn_context(session, new_message):
    """The per-turn facts for the tutor: lesson step, this week's story, last mission, sentence check."""
    p = _kid_prefs(session)
    now = time.time()
    if now - float(p.get("kids_last", 0) or 0) > KIDS_NEW_LESSON_AFTER:
        p["kids_turn"] = 0
    turn = int(p.get("kids_turn", 0) or 0)
    step = KIDS_STEPS[turn] if turn < len(KIDS_STEPS) else KIDS_STEP_FREE
    # 31 Oct 2026 (step 3: memory between lessons): her words are kept per lesson in the session (it survives restarts),
    # and the heroes see the ones from EARLIER lessons. Twin: espaluz-chat kidsMemoryCard.
    if turn == 0:
        p["kids_lesson"] = int(p.get("kids_lesson", 0) or 0) + 1
    lesson = int(p.get("kids_lesson", 1) or 1)
    # Her web lessons are fetched once, at the hello, and kept for the rest of this lesson.
    if turn == 0:
        p["kids_web"] = kids_web_memory(session)
    card = kids_memory_card(p, lesson, p.get("kids_web"))
    words = (new_message or "").strip()
    if words and not words.startswith("/") and words not in [x[1] for x in p.get("kids_said", [])]:
        p["kids_said"] = (p.get("kids_said") or [])[-29:] + [[lesson, words[:120]]]
    p["kids_hold"] = kids_asked_question(new_message)
    heard = card + (kids_heard(new_message) if turn > 0 else "")
    if p["kids_hold"]:
        hello = "Say hello to Alisa in a few words inside the first line, then " if turn == 0 else ""
        out = [heard + f"\nTHIS TURN: Alisa ASKED A QUESTION. {hello}ANSWER IT FIRST, truly and simply, for a 6-7 year old: "
               "2-3 short lines with one real fact (if you are not sure of a fact, say what you do know - never invent). "
               "Stay on HER topic; do not start a game, a story or a new lesson step this turn. "
               f"End with ONE question about the SAME topic she asked about. (The lesson continues next turn with: {step})"]
        if turn == 0:
            out.append(f"THIS WEEK'S STORY (only if it is about what she asked; otherwise ignore it): {kids_week_story()}")
    else:
        # 31 Oct 2026 (web lesson 13:46-13:51, same rules here): the story rode along on EVERY turn, so "quiero jugar un
        # poquitito" became the toucan again, and Titi fell silent for three replies. Story only at the hello and on its
        # own step; both heroes every turn; today's date and Panama's real holidays. Twin: espaluz-chat kidsTurnContext.
        out = [heard + f"\nTHEN, this turn's lesson step (turn {turn + 1} of {len(KIDS_STEPS)}), built on what she just said "
               f"and only if it fits after your first line (skip it after 1 or 4 above) - her idea always wins over the plan: "
               f"{step}"]
        if turn == 0 or step.startswith("THIS WEEK'S STORY"):
            out.append(f"THIS WEEK'S STORY (one line at the hello; the whole story only on its own step; if Alisa already "
                       f"chose a topic, her topic wins): {kids_week_story()}")
    out.append(kids_today())
    out.append('BOTH heroes speak in this reply: at least one "Pere [shot]:" line AND one "Titi [shot]:" line (Titi is the '
               "playful one - let him ask the closing question or make it a little game).")
    # The last mission now travels in the memory card (kids_memory_card): from an earlier lesson, not "another day".
    prev = next((m.get("content", "") for m in reversed(session.get("messages", [])[:-1]) if m.get("role") == "assistant"), "")
    check = kids_sentence_check(prev, new_message) if turn > 0 else ""
    if check:
        out.append(check)
    return "\n".join(out) + "\n"


def kids_tidy(text):
    """How a kids reply looks in the chat (31 Oct 2026, Elena: "kids session is ugly"): no adult "🤖 Espaluz:" header,
    each hero always wears his own badge (🦥 Pere, 🐒 Titi) instead of whatever emoji the model put first, a blank line
    between speakers, no stray ✅ before the question."""
    out = []
    for line in (text or "").split("\n"):
        t = line.strip()
        if not t:
            continue
        m = re.match(r"^[^\wáéíóúñ¡¿]*(Pere|Titi)\s*:\s*", t)
        if m:
            badge = "🦥 Pere" if m.group(1) == "Pere" else "🐒 Titi"
            out.append(f"{badge}: {t[m.end():]}")
        else:
            out.append(re.sub(r"^[^\wáéíóúñ¡¿\"“«(]+", "", t))
    return "\n\n".join(out) or text


def kids_after_reply(session, chat_id, full_reply, media_thread=None):
    """After a kids reply: advance the turn, remember the mission, count the star, unlock Titi's dance every 5 stars."""
    p = _kid_prefs(session)
    turn = int(p.get("kids_turn", 0) or 0)
    p["kids_last"] = time.time()
    # What the heroes understood from her latest words (their first line) goes next to them in her memory.
    said = p.get("kids_said") or []
    if said and len(said[-1]) == 2 and said[-1][0] == p.get("kids_lesson"):
        first = next((l.strip() for l in strip_shot_tags(full_reply or "").split("\n") if l.strip()
                      and "VIDEO SCRIPT" not in l), "")
        said[-1].append(re.sub(r"^[^:]{0,20}:\s*", "", first).split(" / ")[0][:120])
    if p.pop("kids_hold", False):
        if turn == 0:
            p["kids_turn"] = 1  # the hello was folded into the answer; never greet again
        return  # the planned step waits: answering her question was this turn
    p["kids_turn"] = turn + 1
    if turn == 0 and p.get("kids_mission_lesson") not in (None, p.get("kids_lesson")):
        p.pop("kids_mission", None)  # asked about in this hello; a new one comes at the goodbye
    for line in (full_reply or "").split("\n"):
        if re.search(r"misi[oó]n|mission", line, re.I):
            q = re.findall(r"[\"“«]([^\"”»]{5,120})[\"”»]", line)
            p["kids_mission"] = (q[0] if q else re.sub(r"^.*?:\s*", "", strip_shot_tags(line)))[:160]
            p["kids_mission_day"] = datetime.now().strftime("%Y-%m-%d")
            p["kids_mission_lesson"] = p.get("kids_lesson")
            break
    if turn == 0:
        return  # the hello answers no question of hers, so no star yet
    p["kids_stars"] = int(p.get("kids_stars", 0) or 0) + 1
    if p["kids_stars"] % 5:
        return
    stars = p["kids_stars"]

    def _dance():
        if media_thread is not None:
            media_thread.join(timeout=240)  # after the heroes' video, never on top of it
        clip = os.path.join(HERO_DIR, "titi-dance.mp4")
        try:
            with open(clip, "rb") as f:
                bot.send_video(chat_id, f, caption=f"🌟 ¡{stars} estrellas! Titi baila para ti, Alisa. / {stars} stars! Titi dances for you, Alisa! 🐒💃")
            print(f"⭐ kids stars {stars} -> titi-dance unlocked")
        except Exception as e:
            print(f"⚠️ star dance not sent: {e}")
    threading.Thread(target=_dance, daemon=True).start()


def kids_photo_story(photo_bytes):
    """What is in the child's photo, in two short sentences (toy, drawing, food...). Grok sees images on the key the
    bot already has (verified 30 Oct); OpenAI gpt-4o has had no credits since 23 Oct. Returns "" when nobody can see."""
    b64 = base64.b64encode(photo_bytes).decode()
    ask = [{"type": "text", "text": "A 6-year-old girl sent this photo to her Spanish tutors. In 2 short sentences, what is in it? Name the main things and colours. No text reading."},
           {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]
    for url, key, model in (("https://api.x.ai/v1/chat/completions", os.environ.get("XAI_API_KEY"),
                             os.environ.get("XAI_MODEL", "").strip() or "grok-4.20-0309-non-reasoning"),
                            ("https://api.openai.com/v1/chat/completions", OPENAI_API_KEY, "gpt-4o")):
        if not key:
            continue
        try:
            r = requests.post(url, headers={"Authorization": f"Bearer {key}"}, timeout=60,
                              json={"model": model, "max_tokens": 200, "messages": [{"role": "user", "content": ask}]})
            text = (r.json().get("choices") or [{}])[0].get("message", {}).get("content", "")
            if text:
                print(f"🖼️ kids photo seen by {model}")
                return text.strip()
            print(f"⚠️ kids photo {model}: {r.status_code} {r.text[:160]}")
        except Exception as e:
            print(f"⚠️ kids photo {model}: {e}")
    return ""


def apply_kids_switch(user_id, text=None, force=None):
    """'Soy Alisa' / /kids turns Pere + Titi on; 'soy mamá' / /mama turns them off (22 Oct 2026).
    The saved role used to win over 'soy Alisa', so the switch never happened. The parent's role is kept and restored."""
    prefs = user_sessions.get(user_id, {}).get("context", {}).get("user", {}).get("preferences")
    if prefs is None:
        return None
    t = (text or "").lower()
    if (force == "on" or any(k in t for k in KIDS_ON)) and prefs.get("family_role") != "alisa":
        prefs["kids_saved_role"] = prefs.get("family_role")
        prefs["family_role"] = "alisa"
        prefs["kids_turn"], prefs["kids_last"] = 0, 0  # /kids = a new lesson from HELLO (30 Oct 2026)
        return "on"
    if (force == "off" or any(k in t for k in KIDS_OFF)) and prefs.get("family_role") == "alisa":
        prefs["family_role"] = prefs.pop("kids_saved_role", None) or "parent"
        return "off"
    return None


def bulletproof_video_generator(chat_id, full_reply_text):
    print("🚀 ENTERED bulletproof_video_generator")
    try:
        match = re.search(r"\[VIDEO SCRIPT START\](.*?)\[VIDEO SCRIPT END\]", full_reply_text, re.DOTALL)
        if not match:
            print("❌ No [VIDEO SCRIPT START] block found in Claude response.")
            return False

        short_reply = match.group(1).strip()

        # Alisa (22 Oct 2026): each hero speaks his own lines in his own cartoon voice over his talking clip.
        # Any failure falls through to the usual gTTS video below, so she always gets a video.
        if alisa_hero_clip(chat_id, short_reply):
            segments = hero_segments(short_reply, full_reply_text)
            if segments and build_hero_video(segments, "bp_hero_video.mp4"):
                try:
                    with open("bp_hero_video.mp4", "rb") as video_file:
                        bot.send_video(chat_id, video_file, timeout=180)
                    print(f"🦥🐒 Hero voices video sent: {[(w, sh) for w, _, sh in segments]}")
                    return "hero"
                except Exception as hero_err:
                    print(f"⚠️ hero video send failed, using the usual video: {hero_err}")
            else:
                print("⚠️ hero voices unavailable, using the usual video")

        # ENHANCEMENT: Clean text for speech
        short_reply_clean = clean_text_for_speech(short_reply)
        print(f"📝 Cleaned text for video: '{short_reply_clean}'")

        # Generate TTS with cleaned text
        tts = gTTS(text=short_reply_clean, lang="es")
        audio_path = "bp_audio.mp3"
        tts.save(audio_path)
        print(f"🔊 Audio saved: {audio_path}")

        # === STEP 3: Merge with muted 30s avatar video
        base_video = "looped_video.mp4"
        hero_loop = []
        # Alisa (Elena, 22 Oct 2026): her two heroes Pere + Titi are the avatar instead of the EspaLuz loop.
        hero = alisa_hero_clip(chat_id, short_reply)
        if hero:
            base_video, hero_loop = hero, ["-stream_loop", "-1"]  # 5 s clips loop for as long as the voice speaks
            print(f"🦥🐒 Alisa hero clip: {hero}")
        output_video = "bp_video.mp4"

        # Re-encode to 720p. The source avatar loop is 1080p and the old command
        # kept that resolution at default CRF, producing ~2.8 MB for a ~10s clip.
        # Longer tutor replies make longer audio, so the file grew until the
        # Telegram upload hit a write timeout. 720p is more than enough for a
        # phone and cuts the upload to a fraction of the size.
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            *hero_loop,
            "-i", base_video,
            "-i", audio_path,
            "-map", "0:v:0",  # take only video stream from base video
            "-map", "1:a:0",  # take only audio stream from mp3
            "-vf", "scale=-2:720",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "28",
            "-c:a", "aac",
            "-b:a", "96k",
            "-movflags", "+faststart",
            "-shortest",
            output_video
        ]

        print("🎬 Merging audio with looped video using FFmpeg...")
        subprocess.run(ffmpeg_command, check=True)

        size_mb = os.path.getsize(output_video) / (1024 * 1024)
        print(f"🎬 Video encoded: {size_mb:.2f} MB")

        # === STEP 4: Send video to Telegram
        # Explicit generous timeout: telebot's default is far too short for a
        # multi-MB upload from this VM, which is how the write timeout appeared.
        sent = False
        for attempt in (1, 2):
            try:
                with open(output_video, "rb") as video_file:
                    bot.send_video(chat_id, video_file, timeout=180)
                print("📤 Video sent successfully!")
                sent = True
                break
            except Exception as send_err:
                print(f"⚠️ send_video attempt {attempt} failed: {send_err}")
        if not sent:
            raise Exception("send_video failed after 2 attempts")

        # === STEP 5: Cleanup
        os.remove(audio_path)
        os.remove(output_video)
        return True

    except Exception as e:
        print(f"❌ Error in bulletproof_video_generator: {e}")
        return False

def send_full_voice_message(chat_id, full_reply_text):
    """Send the full reply as a voice note. Returns True only if it really sent."""
    mp3_path = "simple_voice.mp3"
    ogg_path = "simple_voice.ogg"
    try:
        # ENHANCEMENT: Clean the full text too
        full_reply_clean = clean_text_for_speech(full_reply_text)
        print(f"🎧 Generating voice with cleaned text, length: {len(full_reply_clean)}")

        tts = gTTS(text=full_reply_clean, lang="es")
        tts.save(mp3_path)

        # Transcode to Opus. Richer tutor replies pushed the mp3 past 1.3 MB and
        # the upload hit a write timeout; opus is both far smaller and the format
        # Telegram actually wants for a voice note. Fall back to the mp3 if
        # ffmpeg is unavailable for any reason.
        upload_path = mp3_path
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", mp3_path, "-c:a", "libopus", "-b:a", "48k", ogg_path],
                capture_output=True, check=True,
            )
            if os.path.exists(ogg_path) and os.path.getsize(ogg_path) > 0:
                upload_path = ogg_path
        except Exception as enc_err:
            print(f"⚠️ Voice opus transcode failed, sending mp3: {enc_err}")

        print(f"🎧 Voice payload: {os.path.getsize(upload_path) / (1024*1024):.2f} MB ({upload_path})")

        # Explicit generous timeout — the default is too short for a multi-MB
        # upload from this VM and surfaced as 'The write operation timed out'.
        sent = False
        for attempt in (1, 2):
            try:
                with open(upload_path, "rb") as f:
                    bot.send_voice(chat_id, f, timeout=180)
                sent = True
                break
            except Exception as send_err:
                print(f"⚠️ send_voice attempt {attempt} failed: {send_err}")

        for leftover in (mp3_path, ogg_path):
            if os.path.exists(leftover):
                os.remove(leftover)

        if sent:
            print("✅ Voice message sent successfully")
            return True
        print("❌ Voice message failed after 2 attempts")
        return False
    except Exception as e:
        print(f"❌ Voice message error: {e}")
        for leftover in (mp3_path, ogg_path):
            if os.path.exists(leftover):
                os.remove(leftover)
        return False

def extract_text_from_image(file_path):
    """Extract text from an image using OCR"""
    try:
        text = pytesseract.image_to_string(Image.open(file_path))
        return text.strip()
    except Exception as e:
        print("OCR error:", e)
        return ""

def process_photo(photo_file):
    """Process photo using GPT-4o Vision - ENHANCED for long texts like book pages"""
    try:
        # Open the image from bytes
        image = Image.open(io.BytesIO(photo_file))

        # ENHANCEMENT: Better preprocessing for book pages
        # Increase resolution limit for better OCR
        max_size = 2048  # Increased from 1024
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.LANCZOS)

        # Convert to base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=95)  # Higher quality
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": """You are an expert at extracting and translating text from images, including full book pages, documents, and handwritten notes. 
                    Extract ALL visible text, preserving the original formatting, paragraphs, and structure.
                    Then provide translations to both Spanish and English."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Extract ALL text from this image. This could be:
                            - A full page from a book
                            - A document with multiple paragraphs
                            - Handwritten notes
                            - Mixed content with titles, subtitles, and body text
                            
                            Preserve the structure and formatting. After extraction, translate everything to both Spanish and English."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"  # Critical for long texts
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 4000  # Increased for long texts
        }

        # 31 Oct 2026: OpenAI-only since forever, dead since its credit ran out on 23 Oct. Paid first (gpt-4o reads long
        # pages best and refuses in a split second when dry), then Grok vision on the key the bot already has (the
        # kids photo path has used it since 30 Oct). A top-up is picked up automatically.
        for url, key, model in (("https://api.openai.com/v1/chat/completions", OPENAI_API_KEY, "gpt-4o"),
                                ("https://api.x.ai/v1/chat/completions", os.environ.get("XAI_API_KEY"),
                                 os.environ.get("XAI_MODEL", "").strip() or "grok-4.20-0309-non-reasoning")):
            if not key:
                continue
            try:
                response = requests.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                                         json={**payload, "model": model}, timeout=90)
                result = response.json()
                extracted_text = ((result.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
                if extracted_text.strip():
                    print(f"🖼️ photo read by {model}")
                    word_count = len(extracted_text.split())
                    return f"📄 Extracted {word_count} words:\n\n{extracted_text}"
                print(f"⚠️ photo {model}: {response.status_code} {response.text[:160]}")
            except Exception as e:  # noqa: BLE001 — try the next provider
                print(f"⚠️ photo {model}: {e}")
        return "❌ No pude leer la foto ahora. / I couldn't read the photo right now. Please try again."

    except Exception as e:
        print(f"Error in GPT-4o image processing: {e}")
        return "❌ Error processing the image. Please try again."

# === MAIN LOGIC ===
def ultimate_multimedia_generator(chat_id, full_reply, short_reply):
    """Generate both video and voice messages with proper error handling"""
    try:
        # First, attempt to generate and send the video
        print("🎬 Starting video generation...")
        video_success = bulletproof_video_generator(chat_id, full_reply)
        
        # Always generate voice message after video attempt, regardless of video success
        print("🎙️ Starting voice message generation...")
        # Report what actually happened: this line used to hard-code "Voice: Sent"
        # even when the upload had just failed, which made the log unusable for
        # answering "did the user get their voice note?"
        # The heroes' video already speaks in their own voices; a gTTS voice note on top is the EspaLuz voice Alisa should not hear.
        voice_success = True if video_success == "hero" else send_full_voice_message(chat_id, full_reply)

        print(
            f"✅ Multimedia generation complete - "
            f"Video: {'Success' if video_success else 'Failed'}, "
            f"Voice: {'Sent' if voice_success else 'Failed'}"
        )
            
    except Exception as e:
        print(f"❌ Critical error in multimedia generation: {e}")
        # Final fallback - just send a simple message
        try:
            bot.send_message(chat_id, "❌ Lo siento, no pude generar contenido multimedia / Sorry, I couldn't generate multimedia content")
        except:
            print("💔 Failed to send error notification")

def process_message(user_input, chat_id, user_id, message_obj):
    """Process incoming message with ultimate multimedia generation"""
    print(f"⭐️ Processing message from user {user_id}: {user_input[:30]}...")

    # Kids layer: an explicit 'soy Alisa' / 'soy mamá' switches the saved role (22 Oct 2026)
    if user_id in user_sessions:
        apply_kids_switch(user_id, user_input)

    # Init session
    is_new_user = user_id not in user_sessions
    if is_new_user:
        user_sessions[user_id] = create_initial_session(user_id, message_obj.from_user, message_obj.chat, user_input)
        print(f"Created new session for user {user_id}")
        try:
            from wiring_emitter import emit_event
            emit_event("user_signup", {
                "user_id": user_id,
                "access_type": "first_message",
                "first_message": user_input[:50],
                "timestamp": datetime.now().isoformat()
            })
        except Exception:
            pass

    session = user_sessions[user_id]
    session["context"]["conversation"]["message_count"] += 1
    session["context"]["conversation"]["last_interaction_time"] = datetime.now().isoformat()

    # Get translation (skip if translation fails)
    translated = translate_to_es_en(user_input)
    if translated:
        bot.send_message(chat_id, f"📝 Traducción:\n{translated}")
        print("Translation sent")
    else:
        print("Translation skipped - API error")

    # Update message history
    session["messages"].append({"role": "user", "content": user_input})

    # Get Claude response with MCP
    print("Requesting Claude response...")
    full_reply, short_reply, thinking_process = ask_claude_with_mcp(session, translated)
    print(f"Received Claude response, length: {len(full_reply)}")

    # Send the main response (30 Oct 2026: shot tags are for the video only; in kids mode the script block is what the
    # video already says, so a 6-7 year old reads the lesson once, without "[VIDEO SCRIPT START]" or "Pere [hello]:")
    shown = strip_shot_tags(full_reply)
    if session.get("context", {}).get("user", {}).get("preferences", {}).get("family_role") == "alisa":
        shown = re.sub(r"\[VIDEO SCRIPT START\].*?\[VIDEO SCRIPT END\]", "", shown, flags=re.DOTALL).strip() or shown
        bot.send_message(chat_id, kids_tidy(strip_markdown_formatting(shown)))
    else:
        bot.send_message(chat_id, f"🤖 Espaluz:\n{strip_markdown_formatting(shown)}")
    print("Main text response sent")

    # Wiring: emit lesson event to CTO AIPA
    try:
        from wiring_emitter import emit_event
        emit_event("lesson_sent", {
            "user_id": user_id,
            "lesson_type": "text",
            "message_count": session.get("context", {}).get("conversation", {}).get("message_count", 0)
        })
    except Exception:
        pass

    # If extended thinking was used, send it as a separate message
    if thinking_process:
        thinking_summary = f"🧠 *Thinking Process*:\n\n{thinking_process[:500]}..."
        if len(thinking_process) > 500:
            thinking_summary += "\n\n(Thinking process summarized for brevity)"
        bot.send_message(chat_id, thinking_summary, parse_mode="Markdown")
        print("Thinking process sent")

    # Update session with Claude's response
    session["messages"].append({"role": "assistant", "content": full_reply})

    # Launch multimedia generation in a thread
    print("Starting multimedia generation thread...")
    media_thread = threading.Thread(
        target=ultimate_multimedia_generator,
        args=(chat_id, full_reply, short_reply),
        daemon=True
    )
    media_thread.start()
    if session["context"]["user"]["preferences"].get("family_role") == "alisa":
        kids_after_reply(session, chat_id, full_reply, media_thread)

    # Update learning data without waiting for multimedia to complete
    print("Updating learning data...")
    family_member = session["context"]["user"]["preferences"]["family_role"]
    learned_items = enhance_language_learning_detection(full_reply, family_member, session)
    session = update_session_learning(session, learned_items)
    session = adapt_learning_path(session, user_input, full_reply)
    print("Learning data updated")

# Only send progress if something was learned
    if learned_items.get("spanish_words") or learned_items.get("grammar_points"):
        progress_payload = {
            "platform_user_id": user_id,
            "platform": "telegram",
            "session_type": "conversation",
            "content": {"topic": "general"},
            "progress_data": {
                "words_learned": len(learned_items.get("spanish_words", [])),
                "grammar_points": len(learned_items.get("grammar_points", []))
            },
            "emotional_tone": session["context"]["emotional_state"]["current_emotion"],
            "duration_minutes": 10
        }
        # post_progress_to_supabase(user_id, progress_payload)  # Disabled - using PostgreSQL

def process_message_with_tracking(user_input, chat_id, user_id, message_obj):
    """Enhanced version of process_message with PostgreSQL tracking"""
    print(f"⭐️ Processing message from user {user_id}: {user_input[:30]}...")
    
    # === DATABASE TRACKING (NEW - Jan 2026) ===
    # Track user and message in PostgreSQL (doesn't affect existing flow)
    if DATABASE_AVAILABLE and db:
        try:
            username = message_obj.from_user.username if message_obj.from_user else None
            first_name = message_obj.from_user.first_name if message_obj.from_user else None
            db.track_user(user_id, username=username, first_name=first_name)
            db.track_message(user_id, 'text')
        except Exception as e:
            print(f"⚠️ DB tracking error (non-fatal): {e}")

    # Kids layer: an explicit 'soy Alisa' / 'soy mamá' switches the saved role (22 Oct 2026)
    if user_id in user_sessions:
        apply_kids_switch(user_id, user_input)

    # Init session
    is_new_user = user_id not in user_sessions
    if is_new_user:
        user_sessions[user_id] = create_initial_session(user_id, message_obj.from_user, message_obj.chat, user_input)
        print(f"Created new session for user {user_id}")
        try:
            from wiring_emitter import emit_event
            emit_event("user_signup", {
                "user_id": user_id,
                "access_type": "first_message",
                "first_message": user_input[:50],
                "timestamp": datetime.now().isoformat()
            })
        except Exception:
            pass

    session = user_sessions[user_id]
    session["context"]["conversation"]["message_count"] += 1
    session["context"]["conversation"]["last_interaction_time"] = datetime.now().isoformat()

    # Get translation (skip if translation fails)
    translated = translate_to_es_en(user_input)
    if translated:
        bot.send_message(chat_id, f"📝 Traducción:\n{translated}")
        print("Translation sent")
    else:
        print("Translation skipped - API error")

    # Update message history
    session["messages"].append({"role": "user", "content": user_input})

    # Get Claude response with MCP
    print("Requesting Claude response...")
    full_reply, short_reply, thinking_process = ask_claude_with_mcp(session, translated)
    print(f"Received Claude response, length: {len(full_reply)}")

    # Send the main response (30 Oct 2026: shot tags are for the video only; in kids mode the script block is what the
    # video already says, so a 6-7 year old reads the lesson once, without "[VIDEO SCRIPT START]" or "Pere [hello]:")
    shown = strip_shot_tags(full_reply)
    if session.get("context", {}).get("user", {}).get("preferences", {}).get("family_role") == "alisa":
        shown = re.sub(r"\[VIDEO SCRIPT START\].*?\[VIDEO SCRIPT END\]", "", shown, flags=re.DOTALL).strip() or shown
        bot.send_message(chat_id, kids_tidy(strip_markdown_formatting(shown)))
    else:
        bot.send_message(chat_id, f"🤖 Espaluz:\n{strip_markdown_formatting(shown)}")
    print("Main text response sent")

    # Wiring: emit lesson event to CTO AIPA
    try:
        from wiring_emitter import emit_event
        emit_event("lesson_sent", {
            "user_id": user_id,
            "lesson_type": "text",
            "message_count": session.get("context", {}).get("conversation", {}).get("message_count", 0)
        })
    except Exception:
        pass

    # If extended thinking was used, send it as a separate message
    if thinking_process:
        thinking_summary = f"🧠 *Thinking Process*:\n\n{thinking_process[:500]}..."
        if len(thinking_process) > 500:
            thinking_summary += "\n\n(Thinking process summarized for brevity)"
        bot.send_message(chat_id, thinking_summary, parse_mode="Markdown")
        print("Thinking process sent")

    # Update session with Claude's response
    session["messages"].append({"role": "assistant", "content": full_reply})

    # 🆕 NEW: Track this conversation in Supabase
    try:
        sync_progress_to_saas(user_id, user_input, full_reply, session)
    except Exception as e:
        print(f"⚠️ Supabase tracking failed (non-critical): {e}")
    
    # 💾 Save session to persistent storage after each conversation
    try:
        save_persistent_sessions()
    except Exception as e:
        print(f"⚠️ Session save failed (non-critical): {e}")

    # Launch multimedia generation in a thread
    print("Starting multimedia generation thread...")
    media_thread = threading.Thread(
        target=ultimate_multimedia_generator,
        args=(chat_id, full_reply, short_reply),
        daemon=True
    )
    media_thread.start()
    if session["context"]["user"]["preferences"].get("family_role") == "alisa":
        kids_after_reply(session, chat_id, full_reply, media_thread)

    # Update learning data
    print("Updating learning data...")
    family_member = session["context"]["user"]["preferences"]["family_role"]
    learned_items = enhance_language_learning_detection(full_reply, family_member, session)
    session = update_session_learning(session, learned_items)
    session = adapt_learning_path(session, user_input, full_reply)
    print("Learning data updated")

    # Enhanced progress tracking
    if learned_items.get("spanish_words") or learned_items.get("grammar_points"):
        print("📊 Learning progress detected")

    # === UNIFIED MEMORY TRACKING (NEW - Jan 2026) ===
    # Store conversation in unified database for cross-platform memory
    if UNIFIED_MEMORY_AVAILABLE:
        try:
            memory = EspaLuzMemory(platform='telegram', platform_user_id=user_id)
            memory.track_message()
            # Store conversation in LangChain memory
            if memory.chat_history:
                memory.chat_history.add_user_message(user_input)
                memory.chat_history.add_ai_message(full_reply)
                # RAG: embed and store both turns for semantic retrieval
                try:
                    from espaluz_rag import save_turn, get_session_id_for_user
                    _rag_sid = get_session_id_for_user('telegram', memory.user_id)
                    # 31 Oct 2026: this printed "saved" for 9 days while every embedding failed - log what happened.
                    _saved = int(save_turn(_rag_sid, 'user', user_input)) + int(save_turn(_rag_sid, 'assistant', full_reply))
                    print(f"{'✅' if _saved == 2 else '⚠️'} RAG embeddings saved {_saved}/2 for session {_rag_sid[:8]}...")
                except Exception as _rag_e:
                    print(f"⚠️ RAG save non-fatal: {_rag_e}")
            # Track vocabulary learned
            if learned_items.get("spanish_words"):
                for word in learned_items["spanish_words"][:5]:
                    try:
                        memory.add_vocab(word, word, "word")
                    except:
                        pass
            # Track emotional state
            emotion = session.get("context", {}).get("emotional_state", {}).get("current_emotion")
            if emotion:
                memory.track_emotion(emotion, user_input[:100])
            print(f"✅ Unified memory updated for {user_id}")
        except Exception as e:
            print(f"⚠️ Unified memory error (non-fatal): {e}")

# === HANDLERS ===
@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = str(message.from_user.id)
    
    # Atlas micro-test: t.me/EspaLuzFamily_bot?start=expat_language_2026-06-28
    start_arg = (message.text or "").split(maxsplit=1)[1].strip() if len((message.text or "").split()) > 1 else ""
    atlas_concept_id = start_arg if start_arg and "_" in start_arg and len(start_arg) <= 64 else None
    
    # Track activity if enhanced brain available
    if ENHANCED_BRAIN_AVAILABLE:
        try:
            track_activity(user_id)
        except:
            pass
    
    # /start used to reset onboarding every time (31 Oct 2026): a returning user lost her country, name and role, and the
    # next message - even a web connect code - was read as "which country?". A finished profile is kept; /profile changes it.
    saved = get_user_onboarding(user_id)
    if saved.get("step") == "complete" and start_arg.lower() != "new":
        who = saved.get("name") or message.from_user.first_name or ""
        where = (saved.get("country") or "").replace("_", " ").title()
        bot.send_message(
            message.chat.id,
            f"👋 ¡Hola de nuevo{', ' + who if who else ''}! / Welcome back{', ' + who if who else ''}!\n"
            + (f"🌍 {where}\n" if where else "")
            + "\nTu perfil y tu progreso siguen guardados. / Your profile and progress are still saved.\n"
            "Escríbeme cuando quieras · /kids para Pere y Titi · /menu para todo.\n"
            "Write to me anytime · /kids for Pere and Titi · /menu for everything.\n"
            "(/country para cambiar el país · to change country · /start new para empezar de cero · to set up again)",
        )
        return

    set_user_onboarding(user_id, {"step": "country"})

    # Start onboarding - ask for country first
    welcome_msg = ONBOARDING_MESSAGES["country"]

    bot.send_message(message.chat.id, welcome_msg)

    # Wiring: emit signup event to CTO AIPA
    try:
        from wiring_emitter import emit_event
        signup_data = {
            "user_id": user_id,
            "access_type": "onboarding_started",
            "timestamp": datetime.now().isoformat(),
        }
        if atlas_concept_id:
            signup_data["atlas_concept_id"] = atlas_concept_id
            signup_data["utm_term"] = atlas_concept_id
        emit_event("user_signup", signup_data)
        if atlas_concept_id:
            emit_event("trial_started", signup_data)
    except Exception:
        pass  # Never crash the bot

@bot.message_handler(commands=["reset"])
def handle_reset(message):
    """Handle /reset command"""
    user_id = str(message.from_user.id)
    user_sessions[user_id] = create_initial_session(user_id, message.from_user, message.chat)
    bot.reply_to(message, "🔄 Tu sesión ha sido reiniciada. ¡Puedes empezar de nuevo! / Your session has been reset. You can start again!")

@bot.message_handler(commands=["progress"])
def handle_progress(message):
    """Handle /progress command to show learning statistics"""
    user_id = str(message.from_user.id)
    if user_id not in user_sessions:
        user_sessions[user_id] = create_initial_session(user_id, message.from_user, message.chat)

    session = user_sessions[user_id]

    # Get family member info
    family_member = session["context"]["user"]["preferences"]["family_role"]
    member_info = FAMILY_MEMBERS.get(family_member, FAMILY_MEMBERS["elena"])

    # Extract learning stats
    spanish_words = len(session["context"]["learning"]["progress"]["vocabulary"]["spanish"]["learned"])
    english_words = len(session["context"]["learning"]["progress"]["vocabulary"]["english"]["learned"])
    grammar_points = len(session["context"]["learning"]["progress"]["grammar"]["spanish"]["learned"])
    total_sessions = session["context"]["learning"]["total_sessions"]

    # Get current learning level
    current_level = "beginner"
    if "learning_path" in session["context"]["learning"]:
        current_level = session["context"]["learning"]["learning_path"]["vocabulary_level"]

    # Format words list if available
    word_examples = ""
    if spanish_words > 0:
        words = session["context"]["learning"]["progress"]["vocabulary"]["spanish"]["learned"]
        word_examples = "\n🔤 Algunas palabras aprendidas / Some learned words: " + ", ".join(words[:5])

    # Get suggested topics
    suggested_topics = []
    if "learning_path" in session["context"]["learning"]:
        suggested_topics = session["context"]["learning"]["learning_path"].get("suggested_topics", [])

    suggested_text = ""
    if suggested_topics:
        suggested_text = "\n\n📋 *Temas sugeridos / Suggested topics:*\n" + "\n".join([f"- {topic}" for topic in suggested_topics])

    # Check for words needing review
    review_needed = []
    if "learning_path" in session["context"]["learning"]:
        review_needed = session["context"]["learning"]["learning_path"].get("review_needed", [])

    review_text = ""
    if review_needed:
        review_text = "\n\n🔄 *Palabras para revisar / Words to review:*\n" + ", ".join(review_needed)

    progress_msg = f"""📊 *Tu progreso de aprendizaje / Your learning progress:*

🇪🇸 Palabras en español / Spanish words: {spanish_words}
🇬🇧 Palabras en inglés / English words: {english_words}
📝 Puntos gramaticales / Grammar points: {grammar_points}
🔢 Sesiones totales / Total sessions: {total_sessions}
📈 Nivel actual / Current level: {current_level.capitalize()}{word_examples}{suggested_text}{review_text}

¡Sigue practicando! / Keep practicing!"""

    bot.reply_to(message, progress_msg, parse_mode="Markdown")

@bot.message_handler(commands=["profile"])
def handle_profile(message):
    """Show the user's current family profile (name, role, age)"""
    user_id = str(message.from_user.id)

    if user_id not in user_sessions:
        user_sessions[user_id] = create_initial_session(user_id, message.from_user, message.chat)

    prefs = user_sessions[user_id]["context"]["user"]["preferences"]
    name = prefs.get("name", "Not set")
    role = prefs.get("family_role", "Not set")
    age = prefs.get("age", "Not set")

    profile_msg = (
        f"👤 *Tu perfil actual / Your current profile:*\n\n"
        f"🧑 Nombre / Name: *{name}*\n"
        f"🎭 Rol / Role: *{role}*\n"
        f"🎂 Edad / Age: *{age}*\n\n"
        f"✏️ Para cambiarlo, usa el comando:\n"
        f"`/family Nombre Rol Edad`\n\n"
        f"Ejemplo: `/family Sofia mother 38`"
    )
    bot.send_message(message.chat.id, profile_msg, parse_mode="Markdown")

@bot.message_handler(commands=["kids"])
def handle_kids(message):
    """Pere + Titi for children 6-7 (22 Oct 2026; 6-7 since 30 Oct): this chat switches to the kids layer and the heroes say hello."""
    user_id = str(message.from_user.id)
    if user_id not in user_sessions:
        user_sessions[user_id] = create_initial_session(user_id, message.from_user, message.chat)
    apply_kids_switch(user_id, force="on")
    # 31 Oct 2026 (Elena: the same introduction every time): the heroes introduce themselves only on the very first
    # lesson; after that a short welcome back, and their first reply brings back something she told them (memory card).
    p = _kid_prefs(user_sessions[user_id])
    if any(p.get(k) for k in ("kids_introduced", "kids_lesson", "kids_said", "kids_turn", "kids_last", "kids_stars")):
        p["kids_introduced"] = True
        save_persistent_sessions()
        bot.send_message(message.chat.id, "🦥 Pere y 🐒 Titi: ¡Hola de nuevo, Alisa! Te estábamos esperando.\n"
                                          "Hello again, Alisa! We were waiting for you.\n\n"
                                          "¿Qué nos cuentas hoy? / What will you tell us today?\n"
                                          "(Mamá / papá: /mama para volver · to go back)")
        return
    p["kids_introduced"] = True
    save_persistent_sessions()
    caption = ("🦥 Pere: ¡Hola! Soy Pere. Hablo despacito y te enseño frases nuevas.\n"
               "Hello! I'm Pere. I speak slowly and I teach you new sentences.\n\n"
               "🐒 Titi: ¡Y yo soy Titi! Me encantan los juegos.\n"
               "And I'm Titi! I love games.\n\n"
               "Escríbenos o mándanos una nota de voz. / Write to us or send us a voice note.\n"
               "(Mamá / papá: /mama para volver · to go back)")
    # The hello is voiced once by the heroes themselves and kept; the silent clip is only the fallback.
    greeting = os.path.join(HERO_DIR, "kids-greeting.mp4")
    if not os.path.exists(greeting):
        bot.send_chat_action(message.chat.id, "record_video")
        if not build_hero_video(hero_segments(caption), greeting):
            greeting = os.path.join(HERO_DIR, "duo-hello.mp4")
    try:
        with open(greeting, "rb") as video:
            bot.send_video(message.chat.id, video, caption=caption, timeout=180)
    except Exception as e:
        print(f"⚠️ /kids hello video failed: {e}")
        bot.send_message(message.chat.id, caption)


@bot.message_handler(commands=["mama"])
def handle_mama(message):
    """Back from Pere + Titi to the parent's own role (the role saved by /kids is restored)."""
    user_id = str(message.from_user.id)
    if user_id in user_sessions:
        apply_kids_switch(user_id, force="off")
        save_persistent_sessions()
    bot.send_message(message.chat.id, "Modo adulto de nuevo. / Adult mode again.\n(/kids para Pere y Titi · for Pere and Titi)")


@bot.message_handler(commands=["family"])
def handle_family(message):
    """Handle /family command to set custom user profile info (name, role, age)"""

    user_id = str(message.from_user.id)
    if user_id not in user_sessions:
        user_sessions[user_id] = create_initial_session(user_id, message.from_user, message.chat)

    # Expected format: /family Name Role Age
    command_parts = message.text.split(maxsplit=3)

    if len(command_parts) == 4:
        _, name, role, age_str = command_parts
        try:
            age = int(age_str)
            user_sessions[user_id]["context"]["user"]["preferences"]["family_role"] = role.lower()
            user_sessions[user_id]["context"]["user"]["preferences"]["name"] = name.capitalize()
            user_sessions[user_id]["context"]["user"]["preferences"]["user_name"] = name.capitalize()  # Also update user_name for prompts!
            user_sessions[user_id]["context"]["user"]["preferences"]["age"] = age

            bot.reply_to(
                message,
                f"✅ Perfil actualizado / Profile updated:\n👤 *{name.capitalize()}* ({role}, {age} años / years old)",
                parse_mode="Markdown"
            )
            return
        except ValueError:
            bot.reply_to(message, "⚠️ Por favor proporciona una edad válida. / Please provide a valid age.")
            return

    # If input is invalid or missing
    example_msg = (
        "👪 *Configura tu perfil familiar / Set your family profile:*\n\n"
        "Usa este formato / Use this format:\n"
        "`/family Name Role Age`\n\n"
        "Ejemplo / Example:\n"
        "`/family Sofia mother 38`\n"
        "`/family Leo child 6`\n"
        "`/family Carlos grandfather 65`"
    )
    bot.reply_to(message, example_msg, parse_mode="Markdown")

@bot.message_handler(commands=["connect"])
def handle_connect(message):
    try:
        parts = message.text.strip().split(" ")
        if len(parts) < 2:
            bot.reply_to(message, "❗ Please provide your connection code. Example:\n/connect ABC123")
            return

        code = parts[1].strip()
        if not code or len(code) < 3:
            bot.reply_to(message, "❌ Invalid code. Please try again.")
            return

        platform_user_id = str(message.from_user.id)
        platform_username = message.from_user.username or ""

        payload = {
            "code": code,
            "telegram_user_id": platform_user_id,
            "telegram_username": platform_username
        }

        # 🔍 Debug logs to check if everything is correct
        print("📤 Sending connect payload:", payload)
        # Supabase key check removed - using PostgreSQL

        # 31 Oct 2026: this was stubbed out with "the Supabase project is NXDOMAIN" - it is alive (the web app and the
        # classroom run on it), so a valid code from the dashboard was answered "nothing to connect" and never sent.
        try:
            r = requests.post(
                f"{SAAS_FUNCTIONS_URL}/connect-bot",
                json=payload,
                headers={"Authorization": f"Bearer {os.environ.get('SUPABASE_ANON_KEY')}",
                         "Content-Type": "application/json"},
                timeout=15,
            )
        except requests.RequestException as e:
            print(f"❌ /connect: web app unreachable: {e}")
            bot.reply_to(message, "⚠️ No pude llegar a la web ahora. Inténtalo en un minuto.\n"
                                  "⚠️ I couldn't reach the web app right now. Try again in a minute.")
            return
        print(f"🔗 /connect {code}: {r.status_code} {r.text[:200]}")
        if r.status_code == 200:
            bot.reply_to(message, "✅ ¡Conectado! Tu Telegram y tu panel web ya están unidos.\n"
                                  "✅ Connected! Your Telegram and your web dashboard are linked.\n\n"
                                  "Tus próximas prácticas aparecerán en la web. / Your next practice shows up on the web.")
        elif r.status_code == 404:
            bot.reply_to(message, "❌ Ese código no vale o ya caducó (dura 10 minutos).\n"
                                  "❌ That code is wrong or expired (it lasts 10 minutes).\n\n"
                                  "Genera uno nuevo en la web y envía /connect CÓDIGO. / Make a new one on the web and send /connect CODE.")
        else:
            bot.reply_to(message, "⚠️ La web no pudo conectar ahora. Inténtalo otra vez en un minuto.\n"
                                  "⚠️ The web app could not connect right now. Please try again in a minute.")

    except Exception as e:
        print("❌ Exception in /connect:", str(e))
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=["help"])
def handle_help(message):
    if ENHANCED_BRAIN_AVAILABLE:
        help_text = """🌟 *EspaLuz — All Commands*

━━━━━━━━━━━━━━━━━━━━━━━━
📱 *SETUP*
━━━━━━━━━━━━━━━━━━━━━━━━
/start — Welcome & quick start
/family Name Role Age — Set profile
/profile — View your profile
/reset — Clear conversation

━━━━━━━━━━━━━━━━━━━━━━━━
💬 *LEARNING*
━━━━━━━━━━━━━━━━━━━━━━━━
Just chat! Text, voice 🎤, photos 📷
/progress — Your learning stats

━━━━━━━━━━━━━━━━━━━━━━━━
🆘 *REAL-LIFE HELP*
━━━━━━━━━━━━━━━━━━━━━━━━
/help_banking — Bank phrases
/help_medical — Healthcare
/help_school — School vocab
/help_shopping — Shopping
/help_transport — Getting around
/help_emergency — 🚨 Urgent!

━━━━━━━━━━━━━━━━━━━━━━━━
🌎 *CULTURE & SLANG*
━━━━━━━━━━━━━━━━━━━━━━━━
/slang panama — Panamanian expressions
/slang mexico — Mexican slang
/slang colombia — Colombian slang
/slang argentina — Argentine slang
/country NAME — Set your country

━━━━━━━━━━━━━━━━━━━━━━━━
🏢 *ORGANIZATIONS*
━━━━━━━━━━━━━━━━━━━━━━━━
/org CODE — Enter org code
/feedback — Share experience
/refer — Referral program
/metrics — Community stats

━━━━━━━━━━━━━━━━━━━━━━━━
🔐 *ACCOUNT*
━━━━━━━━━━━━━━━━━━━━━━━━
/trial — Check free trial status
/pagar — Pay $11 via PagueloFacil (30 days)
/subscribe — PayPal & payment options
/link — Link PayPal Subscription ID
/connect CODE — Web dashboard

━━━━━━━━━━━━━━━━━━━━━━━━
/menu — Full detailed menu

¡Empecemos! / Let's learn! 🚀"""
    else:
        help_text = """🌟 EspaLuz Bot – Available Commands

/start – Start the bot  
/reset – Reset the conversation  
/progress – View your learning progress  
/profile – Set your name, role, and age  
/link – Link your Subscription ID  
/connect – Connect to your web dashboard  
/help – Show this help message

💬 You can send me text or voice messages in Russian, Spanish, or English.  
📸 You can also send pictures of text (menus, signs, etc.) and I'll translate them instantly.

📊 How to connect your web dashboard:  
1️⃣ Visit https://lovable.dev and go to the Tu Progreso section  
2️⃣ Click Conectar Telegram to generate your 6-digit code  
3️⃣ Then type /connect YOURCODE here in the chat

🔐 To unlock all premium features:  
1️⃣ Subscribe via PayPal  
2️⃣ Send your Subscription ID (I-XXXX) to activate  
3️⃣ Then set up your profile using /profile

Let's learn Spanish together — anywhere, anytime! 💬"""
        bot.reply_to(message, help_text)

# =============================================================================
# NEW ENHANCED COMMANDS (Added January 2026)
# =============================================================================

@bot.message_handler(commands=["help_banking"])
def handle_help_banking(message):
    """Banking help phrases"""
    if ENHANCED_BRAIN_AVAILABLE:
        bot.reply_to(message, HELP_BANKING, parse_mode="Markdown")
    else:
        bot.reply_to(message, "🏦 Banking help not available. Update your bot modules.")

@bot.message_handler(commands=["help_medical"])
def handle_help_medical(message):
    """Medical/healthcare help phrases"""
    if ENHANCED_BRAIN_AVAILABLE:
        bot.reply_to(message, HELP_MEDICAL, parse_mode="Markdown")
    else:
        bot.reply_to(message, "🏥 Medical help not available. Update your bot modules.")

@bot.message_handler(commands=["help_school"])
def handle_help_school(message):
    """School-related help phrases"""
    if ENHANCED_BRAIN_AVAILABLE:
        bot.reply_to(message, HELP_SCHOOL, parse_mode="Markdown")
    else:
        bot.reply_to(message, "🏫 School help not available. Update your bot modules.")

@bot.message_handler(commands=["help_shopping"])
def handle_help_shopping(message):
    """Shopping help phrases"""
    if ENHANCED_BRAIN_AVAILABLE:
        bot.reply_to(message, HELP_SHOPPING, parse_mode="Markdown")
    else:
        bot.reply_to(message, "🛒 Shopping help not available. Update your bot modules.")

@bot.message_handler(commands=["help_transport"])
def handle_help_transport(message):
    """Transportation help phrases"""
    if ENHANCED_BRAIN_AVAILABLE:
        bot.reply_to(message, HELP_TRANSPORT, parse_mode="Markdown")
    else:
        bot.reply_to(message, "🚗 Transport help not available. Update your bot modules.")

@bot.message_handler(commands=["help_emergency"])
def handle_help_emergency(message):
    """Emergency help phrases - PRIORITY"""
    if ENHANCED_BRAIN_AVAILABLE:
        bot.reply_to(message, HELP_EMERGENCY, parse_mode="Markdown")
    else:
        emergency_basic = """🚨 *EMERGENCY PHRASES*
        
¡AYUDA! = HELP!
¡Llame a la policía! = Call the police!
Necesito una ambulancia = I need an ambulance
📞 Emergency: 911"""
        bot.reply_to(message, emergency_basic, parse_mode="Markdown")

@bot.message_handler(commands=["slang"])
def handle_slang(message):
    """Show local slang for a country - supports all 21 Spanish-speaking countries"""
    if not ENHANCEMENTS_AVAILABLE:
        bot.reply_to(message, "Slang module not available.")
        return
    
    from espaluz_enhancements import COUNTRY_CONTEXTS_FULL
    
    parts = message.text.split()
    
    # Country aliases for common names
    country_aliases = {
        "el_salvador": "el_salvador", "elsalvador": "el_salvador", "salvador": "el_salvador",
        "costa_rica": "costa_rica", "costarica": "costa_rica",
        "dominican_republic": "dominican_republic", "dominicana": "dominican_republic", "dr": "dominican_republic",
        "puerto_rico": "puerto_rico", "puertorico": "puerto_rico", "pr": "puerto_rico",
        "equatorial_guinea": "equatorial_guinea", "guinea": "equatorial_guinea",
    }
    
    if len(parts) > 1:
        # Handle multi-word countries like "El Salvador"
        country_raw = "_".join(parts[1:]).lower().strip()
        country = country_aliases.get(country_raw, country_raw)
        
        if country in COUNTRY_CONTEXTS_FULL:
            ctx = COUNTRY_CONTEXTS_FULL[country]
            flag = ctx.get("flag", "")
            name = ctx.get("name", country.replace("_", " ").title())
            slang_list = ctx.get("slang", [])
            greeting = ctx.get("greeting", "¡Hola!")
            currency = ctx.get("currency", "Local currency")
            emergency = ctx.get("emergency", "911")
            
            response = f"{flag} SLANG & PRACTICALITIES: {name}\n\n"
            response += f"👋 Common greeting: {greeting}\n\n"
            response += "🗣️ Local slang:\n"
            if isinstance(slang_list, dict):
                for word, meaning in slang_list.items():
                    response += f"  • {word} = {meaning}\n"
            else:
                for word in slang_list:
                    response += f"  • {word}\n"
            response += f"\n💰 Currency: {currency}"
            if isinstance(emergency, dict):
                response += f"\n📞 Emergency: {emergency.get('police', '911')} (police), {emergency.get('ambulance', '911')} (ambulance)"
            else:
                response += f"\n📞 Emergency: {emergency}"
            response += "\n\n💡 Tip: Use these with locals to sound more natural!"
            
            bot.reply_to(message, response)
        else:
            # Country not found - show available options
            available = ", ".join(sorted(COUNTRY_CONTEXTS_FULL.keys())[:10])
            bot.reply_to(message, f"Country '{country_raw}' not found.\n\nAvailable: {available}...")
    else:
        # No country specified - use user's current country or show list
        user_id = str(message.from_user.id)
        user_country = "panama"  # Default
        if user_id in user_sessions:
            user_country = user_sessions[user_id]["context"]["user"]["preferences"].get("country", "panama")
        
        if user_country in COUNTRY_CONTEXTS_FULL:
            ctx = COUNTRY_CONTEXTS_FULL[user_country]
            flag = ctx.get("flag", "")
            name = ctx.get("name", user_country.replace("_", " ").title())
            slang_list = ctx.get("slang", [])
            greeting = ctx.get("greeting", "¡Hola!")
            currency = ctx.get("currency", "Local currency")
            
            response = f"{flag} SLANG & PRACTICALITIES: {name}\n\n"
            response += f"👋 Common greeting: {greeting}\n\n"
            response += "🗣️ Local slang:\n"
            if isinstance(slang_list, dict):
                for word, meaning in slang_list.items():
                    response += f"  • {word} = {meaning}\n"
            else:
                for word in slang_list:
                    response += f"  • {word}\n"
            response += f"\n💰 Currency: {currency}"
            response += "\n\n💡 Other countries: /slang [country]\n"
            response += "Examples: /slang mexico, /slang el salvador, /slang argentina"
            
            bot.reply_to(message, response)
        else:
            # Fallback - show list of countries
            countries = list(COUNTRY_CONTEXTS_FULL.keys())[:15]
            response = "🌎 Available slang for 21 countries!\n\n"
            response += "Usage: /slang [country]\n\n"
            response += "Examples:\n"
            response += "• /slang mexico\n"
            response += "• /slang el salvador\n"
            response += "• /slang argentina\n"
            response += "• /slang colombia\n"
            response += "• /slang spain\n"
            bot.reply_to(message, response)

@bot.message_handler(commands=["org"])
def handle_org(message):
    """Handle organization code for pilot programs"""
    if not ENHANCED_BRAIN_AVAILABLE:
        bot.reply_to(message, "Organization codes not available.")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        # Real codes are deliberately NOT listed here. Each one is a paid benefit
        # granted to a specific partner organisation and is delivered privately in
        # that partner's own email; printing the list would let anyone claim a
        # 45-90 day trial. Only the FORMAT is shown.
        # The placeholder is in backticks because Telegram Markdown reads
        # _underscores_ as italic markers and would eat them.
        bot.reply_to(message, """🏢 *Organization code / Código de organización*

Usage: `/org SU_CODIGO`

Su organización (colegio, cámara o empresa) le entrega el código.
Escríbalo tal cual: en MAYÚSCULAS y con guion bajo.

Your organization gives you the code. Type it exactly as received:
uppercase, with the underscore.

¿No tiene código? / No code yet?
Pregunte a su colegio o cámara — o use /trial para la prueba estándar.""", parse_mode="Markdown")
        return
    
    code = parts[1].upper().strip()
    org = validate_org_code(code)
    
    if org:
        user_id = str(message.from_user.id)
        track_activity(user_id, code)
        
        response = f"""✅ *{org['welcome_message']}*

🏢 Organization: {org['name']}
📅 Trial Period: {org['trial_days']} days
🌎 Country: {org['country']}

You now have extended access! Start chatting to learn."""
        bot.reply_to(message, response, parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Invalid organization code.\n\nPlease check with your organization for the correct code.")

@bot.message_handler(commands=["feedback"])
def handle_feedback(message):
    """Collect user feedback and testimonials"""
    feedback_prompt = """💬 *We'd love your feedback!*

Please reply with:
• ⭐ Your rating (1-5 stars)
• 💬 A short sentence about your experience
• ✅ "Share" if we can use it publicly, or "Private"

*Example:*
"5 ⭐ EspaLuz helped my whole family adapt to Panama! Share"

Your feedback helps other expat families discover us. Thank you! 🙏"""
    bot.reply_to(message, feedback_prompt, parse_mode="Markdown")

@bot.message_handler(commands=["metrics"])
def handle_metrics(message):
    """Show analytics metrics (for admin/pilots)"""
    if not ENHANCED_BRAIN_AVAILABLE:
        bot.reply_to(message, "Metrics not available.")
        return
    
    try:
        metrics = get_analytics_metrics()
        
        response = f"""📊 *EspaLuz Community Metrics*

👥 Total Users: {metrics['total_users']}
📈 Weekly Active: {metrics['weekly_active_users']}
🔄 30-Day Retention: {metrics['retention_30_day']}
🏢 Organizations Piloting: {metrics['organizations_piloting']}
⭐ Testimonials Collected: {metrics['testimonials_collected']}
🔗 Referrals: {metrics['referrals']}

_Updated in real-time_"""
        bot.reply_to(message, response, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Error getting metrics: {e}")
        bot.reply_to(message, "❌ Error loading metrics.")

@bot.message_handler(commands=["country"])
def handle_country(message):
    """Set user's country context for localized vocabulary"""
    if not ENHANCED_BRAIN_AVAILABLE:
        bot.reply_to(message, "Country context not available.")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        countries = "panama, mexico, colombia, argentina, spain, costa_rica, peru, chile, ecuador"
        bot.reply_to(message, f"""🌎 *Set your country for local vocabulary*

Usage: /country COUNTRY_NAME

Available countries:
{countries}

Example: /country panama

I'll use local expressions and cultural tips!""", parse_mode="Markdown")
        return
    
    country_name = "_".join(parts[1:]).lower().strip()  # Handle multi-word: "El Salvador" -> "el_salvador"
    
    # Map common names
    # All 21 Spanish-speaking countries (with aliases)
    country_map = {
        # Central America
        "panama": "panama", "panamá": "panama",
        "costa_rica": "costa_rica", "costarica": "costa_rica",
        "el_salvador": "el_salvador", "elsalvador": "el_salvador", "salvador": "el_salvador",
        "guatemala": "guatemala",
        "honduras": "honduras",
        "nicaragua": "nicaragua",
        # Mexico
        "mexico": "mexico", "méxico": "mexico",
        # South America
        "colombia": "colombia",
        "venezuela": "venezuela",
        "ecuador": "ecuador",
        "peru": "peru", "perú": "peru",
        "bolivia": "bolivia",
        "chile": "chile",
        "argentina": "argentina",
        "uruguay": "uruguay",
        "paraguay": "paraguay",
        # Caribbean
        "cuba": "cuba",
        "dominican_republic": "dominican_republic", "dominicana": "dominican_republic", "rd": "dominican_republic",
        "puerto_rico": "puerto_rico", "puertorico": "puerto_rico",
        # Europe/Africa
        "spain": "spain", "españa": "spain",
        "equatorial_guinea": "equatorial_guinea", "guinea_ecuatorial": "equatorial_guinea",
    }
    
    if country_name in country_map:
        normalized_country = country_map[country_name]
        # Get context from enhancement module if available
        if ENHANCEMENTS_AVAILABLE:
            from espaluz_enhancements import COUNTRY_CONTEXTS_FULL
            context = COUNTRY_CONTEXTS_FULL.get(normalized_country, {})
        else:
            context = get_country_context(Country.PANAMA)  # Fallback
        
        user_id = str(message.from_user.id)
        if user_id in user_sessions:
            user_sessions[user_id]["context"]["user"]["preferences"]["country"] = country_name
        
        # Escape underscores for Markdown
        display_country = country_name.replace("_", " ").title()
        
        response = f"""✅ Country set: {context.get('flag', '')} {context.get('name', display_country)}

💰 Currency: {context.get('currency', 'Local currency')}
🕐 Timezone: {context.get('timezone', 'Local time')}

I'll now use local vocabulary and expressions!

Try: /slang to see local expressions."""
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, f"❌ Country '{country_name}' not found.\n\nTry: panama, mexico, colombia, argentina, spain, costa_rica")

@bot.message_handler(commands=["refer"])
def handle_refer(message):
    """Show referral program info"""
    user_id = str(message.from_user.id)
    
    # Get referral stats if available
    referral_count = 0
    if ENHANCED_BRAIN_AVAILABLE:
        try:
            if user_id in analytics.data.get("referrals", {}):
                referral_count = len(analytics.data["referrals"][user_id])
        except:
            pass
    
    response = f"""🔗 *Share EspaLuz with Friends!*

*How it works:*
1. Share EspaLuz with friends
2. When they subscribe, you BOTH get 1 month FREE
3. No limit on referrals!

*Your referral stats:*
• Friends referred: {referral_count}
• Free months earned: {referral_count}

To refer someone:
1. Tell them to message @EspaLuzBot
2. Have them mention your username when subscribing

Thank you for spreading the word! 🙏"""
    bot.reply_to(message, response, parse_mode="Markdown")

@bot.message_handler(commands=["menu"])
def handle_menu(message):
    """Show the complete menu - split if too long for Telegram"""
    if ENHANCED_BRAIN_AVAILABLE:
        # Plain text - no parse_mode to avoid underscore issues
        menu_clean = MENU_TEXT.replace('*', '').replace('_', ' ')
        
        # Telegram limit is 4096 chars - split if needed
        if len(menu_clean) > 4000:
            # Split into parts
            parts = menu_clean.split('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
            current_msg = ""
            for part in parts:
                if len(current_msg) + len(part) + 35 < 4000:
                    current_msg += part + '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
                else:
                    if current_msg:
                        bot.send_message(message.chat.id, current_msg.strip())
                    current_msg = part + '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
            if current_msg:
                bot.send_message(message.chat.id, current_msg.strip())
        else:
            bot.reply_to(message, menu_clean)
    else:
        # Fallback to basic help
        handle_help(message)

# =============================================================================
# END OF NEW ENHANCED COMMANDS
# =============================================================================

def whisper_hint(session):
    """31 Oct 2026 ("hear her better", twin of voice-to-text whisperHint): Whisper takes a `prompt` that tells it what
    to expect, and we never sent one - a 6-year-old's answers came back as "Starberry" or Portuguese. In Alisa mode the
    hint is the heroes' last question (like a teacher who knows what she just asked); otherwise a language hint."""
    base = "Spanish and English, sometimes Russian. "
    try:
        if (session or {}).get("context", {}).get("user", {}).get("preferences", {}).get("family_role") != "alisa":
            return base
        last = next((m.get("content", "") for m in reversed(session.get("messages", [])) if m.get("role") == "assistant"), "")
        lines = [re.sub(r"^[^:\[]*(\[[^\]]*\])?:\s*", "", l).strip() for l in strip_shot_tags(last).split("\n")]
        lines = [l for l in lines if l and "VIDEO SCRIPT" not in l]
        question = next((l for l in reversed(lines) if "?" in l), lines[-1] if lines else "")
        return f"A 6-year-old girl answers Pere and Titi in Spanish or English. They just asked: {question[:200]}"
    except Exception:  # noqa: BLE001 — a hint must never break transcription
        return base


def _echoes_hint(text, hint):
    """With a hint and near-silence Whisper can "hear" the hint itself: a transcript of only hint words is dropped."""
    t = _kid_words(text)
    if len(t) < 3:
        return False
    h = set(_kid_words(hint))
    return sum(1 for w in t if w in h) / len(t) > 0.8


# Whisper's known phantoms on silence or noise (measured 31 Oct on Groq whisper-large-v3-turbo: 3 s of silence ->
# "Thank you." / "you", pink noise -> "I'm not sure."; no_speech_prob is always 0 there, so only the text can tell).
# A bare "gracias" is NOT on the list: a child may really say it. Twin: voice-to-text PHANTOMS.
_PHANTOMS = {"thank you", "you", "thanks for watching", "thank you for watching", "im not sure", "i m not sure",
             "subtitles by the amara org community", "gracias por ver el video",
             "subtitulos realizados por la comunidad de amara org", ""}


def transcribe_audio(audio_path: str, hint: str = "Spanish and English, sometimes Russian. ") -> str:
    """Transcribe a voice note: Groq Whisper first, OpenAI Whisper as the backup (23 Oct 2026).

    It was OpenAI only. When OpenAI ran out of credits on 23 Oct (429 insufficient_quota) every voice note got
    "No pude transcribir este mensaje de voz", while the Groq key in .env worked. Same order as OpenClaw's audio
    chain (groq whisper-large-v3-turbo → openai). Returns None only when every provider failed.
    """
    providers = [
        ("groq", "https://api.groq.com/openai/v1/audio/transcriptions", os.getenv("GROQ_API_KEY"), "whisper-large-v3-turbo"),
        ("openai", "https://api.openai.com/v1/audio/transcriptions", os.getenv("OPENAI_API_KEY"), "whisper-1"),
    ]
    for name, url, key, model in providers:
        if not key:
            continue
        try:
            with open(audio_path, "rb") as f:
                res = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {key}"},
                    files={"file": (os.path.basename(audio_path), f)},
                    data={"model": model, "response_format": "text", "prompt": hint, "temperature": "0"},
                    timeout=60,
                )
            if res.status_code == 200 and res.text.strip():
                if name != "groq":
                    print(f"🎙️ Transcription via {name} (groq failed)")
                if _echoes_hint(res.text, hint) or " ".join(_kid_words(res.text)) in _PHANTOMS:
                    print(f"🎙️ silence phantom or hint echo -> treated as silence: {res.text.strip()[:120]}")
                    return None
                print(f"🎙️ hint: {hint[:120]}")
                return res.text.strip()
            print(f"❌ Transcription error ({name}): {res.status_code} {res.text[:160]}")
        except Exception as e:
            print(f"❌ Transcription error ({name}): {e}")
    return None

@bot.message_handler(commands=["link"])
def handle_link(message):
    link_msg = f"""📩 Link Your Subscription

You're currently on a FREE TRIAL - enjoy all features!

After trial ends:
• Monthly: $11/month (includes 14-day FREE trial!)

🇵🇦 PagueloFacil (Panama cards, one-time):
  Send /pagar for secure checkout link ($11 → 30 days)

💳 PayPal (monthly subscription):
{PAYPAL_SUBSCRIPTION_LINK}

🔑 After subscribing, send me your Subscription ID to activate!
   Find it: PayPal → Settings → Payments → Automatic payments
   Format: I-XXXXXXXXXXXX

Questions? Contact @revicheva"""
    bot.send_message(message.chat.id, link_msg)


# === DEMO MODE COMMANDS (NEW - Jan 2026) ===
@bot.message_handler(commands=["demo"])
def handle_demo(message):
    """Toggle demo mode for workshop presentations"""
    user_id = str(message.from_user.id)
    
    if not PAYPAL_SYSTEM_AVAILABLE or not demo_mode:
        bot.reply_to(message, "⚠️ Demo mode not available.")
        return
    
    # Check if user wants to turn off demo
    args = message.text.split()
    if len(args) > 1 and args[1].lower() == "off":
        response = demo_mode.deactivate_demo(user_id)
        bot.reply_to(message, response)
        return
    
    # Activate demo mode
    if demo_mode.is_demo_active(user_id):
        response = demo_mode.deactivate_demo(user_id)
    else:
        response = demo_mode.activate_demo(user_id)
    
    bot.reply_to(message, response)


@bot.message_handler(commands=["scenarios"])
def handle_scenarios(message):
    """Show demo scenarios for presenters"""
    if demo_mode:
        bot.reply_to(message, demo_mode.get_demo_scenarios())
    else:
        bot.reply_to(message, "⚠️ Demo mode not available.")


# === SUBSCRIPTION COMMANDS (NEW - Jan 2026) ===

# =============================================================================
# CONVERSATION MODE - Real-time translation like Google Translate
# =============================================================================

CONVO_ACTIVATED_MSG = """🎙️ *CONVERSATION MODE ACTIVATED*

How it works:
1. Send a voice message in ANY language
2. I translate it and speak it back

🇷🇺 Russian → 🇪🇸 Spanish *and* 🇬🇧 English (both text + voice)
🇬🇧 English → 🇪🇸 Spanish
🇪🇸 Spanish → 🇬🇧 English

Perfect for: pharmacy, doctor, school meetings, shopping, immigration.

/convo off — back to tutor mode
/convo es — translate TO Spanish
/convo en — translate TO English

🎤 Start speaking now!"""

CONVO_DEACTIVATED_MSG = """🔇 *Conversation mode OFF* — back to full tutor mode.

You get explanations, grammar, culture and video replies again.
Send /convo on any time you need fast translation."""


@bot.message_handler(commands=["convo"])
def handle_convo(message):
    """Toggle conversation mode for real-time voice translation"""
    user_id = str(message.from_user.id)
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []

    if args and args[0].lower() in ("off", "stop", "end", "0"):
        result = conversation_mode.deactivate(user_id)
        count = result.get("message_count", 0) if isinstance(result, dict) else 0
        tail = f"\n\nTranslations this session: {count}" if count else ""
        bot.send_message(message.chat.id, CONVO_DEACTIVATED_MSG + tail, parse_mode="Markdown")
        print(f"CONVO ACTION user={user_id} deactivated count={count}", flush=True)
        return

    # Turning convo mode ON is a paid action — same gate as voice/text/photo.
    # enforce_learning_access covers BOTH rails (PayPal + PagueloFacil) and trial.
    if not enforce_learning_access(message, user_id):
        return

    # Target language applies to Spanish/English input.
    # Russian always returns BOTH Spanish and English.
    target_lang = "es"  # Default
    if args:
        arg = args[0].lower()
        if arg in ["es", "spanish", "español"]:
            target_lang = "es"
        elif arg in ["en", "english", "inglés", "ingles"]:
            target_lang = "en"

    conversation_mode.activate(user_id, target_lang)
    print(f"CONVO ACTION user={user_id} activated target={target_lang}", flush=True)
    bot.send_message(message.chat.id, CONVO_ACTIVATED_MSG, parse_mode="Markdown")


def _convo_translate(text, source_lang, target_lang):
    """
    One translation on the fleet fallback spine: Claude -> the 4-provider chain.
    Returns the translated string, or None when every provider failed.

    Note the fallback triggers on ANY Claude exception, not a status allowlist:
    the previous version only retried on {400, 529, 503}, so a 404 from a stale
    CLAUDE_MODEL_NAME killed the whole translation with no fallback.

    Changed 2026-08-16 to match the WhatsApp twin (whatsapp_convo_mode.py):
    the hand-rolled Groq -> OpenAI ladder below Claude became one chain call.
    Two reasons it was worth replacing rather than leaving alone:

    - Its Groq leg was the FIRST fallback and had never once run — this repo's
      .env carried GROQ_MODEL but no GROQ_API_KEY, so the `if groq_key` guard
      was always false. Translations silently went Claude -> gpt-4o-mini.
    - gpt-4o-mini was hard-coded, so a retirement there would have repeated
      exactly the llama-3.3-70b outage this whole change came from.

    A failed translation is not cosmetic: the family gets one half of a
    bilingual conversation missing.
    """
    import anthropic

    if source_lang == target_lang:
        return text

    prompt = get_quick_translate_prompt(text, source_lang, target_lang)
    msgs = [{"role": "user", "content": prompt}]

    try:
        from llm_chain import free_tier
        if free_tier():  # 30 Oct 2026: free mode = the fallback below answers, Claude not first
            raise Exception("MODEL_TIER=free")
        client = anthropic.Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))
        response = client.messages.create(model=CLAUDE_MODEL, max_tokens=500, messages=msgs)  # tier-gated
        return response.content[0].text.strip()
    except Exception as claude_err:
        print(f"Convo Claude failed ({source_lang}->{target_lang}): {claude_err}", flush=True)

    try:
        from llm_chain import PROFILE_FALLBACK, complete

        translation, errors = complete(None, prompt, max_tokens=500,
                                       order=PROFILE_FALLBACK)
        if translation:
            print(f"✅ Convo fallback translation OK {source_lang}->{target_lang}", flush=True)
            return translation.strip()
        print(f"❌ Convo fallback exhausted {source_lang}->{target_lang}: "
              f"{'; '.join(errors)[:200]}", flush=True)
    except Exception as chain_err:
        print(f"❌ Convo fallback chain error: {chain_err}", flush=True)

    return None


def _convo_voice_note(text, lang, slot_id):
    """
    Render `text` as a Telegram-ready OGG voice note in `lang`.

    `slot_id` MUST be unique per clip. Neural TTS names its output
    neural_tts_{message_id}.mp3, so reusing one id would make the English clip
    silently overwrite the Spanish one when both are rendered for one message.
    Returns the .ogg path, or None.
    """
    mp3_path = f"convotts_{slot_id}.mp3"
    ogg_path = f"convotts_out_{slot_id}.ogg"

    rendered = False
    if NEURAL_TTS_AVAILABLE:
        try:
            neural_path = generate_voice_sync(text, lang=lang, style="conversation", message_id=slot_id)
            if neural_path:
                if neural_path != mp3_path:
                    import shutil
                    shutil.copy(neural_path, mp3_path)
                    os.remove(neural_path)
                rendered = True
            else:
                print(f"Neural TTS returned None for {lang}, using gTTS", flush=True)
        except Exception as e:
            print(f"Neural TTS failed for {lang}: {e}, using gTTS", flush=True)

    if not rendered:
        try:
            gTTS(text=text, lang=lang, slow=False).save(mp3_path)
        except Exception as e:
            print(f"gTTS failed for {lang}: {e}", flush=True)
            return None

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", mp3_path, "-c:a", "libopus", "-b:a", "64k", ogg_path],
            capture_output=True, check=True,
        )
    except Exception as e:
        print(f"ffmpeg convo encode failed for {lang}: {e}", flush=True)
        ogg_path = None

    if os.path.exists(mp3_path):
        os.remove(mp3_path)
    return ogg_path


def handle_conversation_voice(message):
    """Fast voice translation for conversation mode"""
    import anthropic
    from gtts import gTTS
    import subprocess
    import os

    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    
    try:
        # 1. Download and convert voice
        file_info = bot.get_file(message.voice.file_id)
        voice_file = bot.download_file(file_info.file_path)
        
        temp_ogg = f"convo_{message.message_id}.ogg"
        temp_mp3 = f"convo_{message.message_id}.mp3"
        
        with open(temp_ogg, "wb") as f:
            f.write(voice_file)
        
        subprocess.run(["ffmpeg", "-y", "-i", temp_ogg, temp_mp3], 
                      capture_output=True, check=True)
        
        # 2. Transcribe with Whisper
        transcription = transcribe_audio(temp_mp3)
        if not transcription:
            bot.reply_to(message, "❌ Couldn't hear that. Try again?")
            return
        
        # 3. Detect language
        detected_lang = detect_language(transcription)

        # 4. Translate and speak.
        #    Russian is the bridge case: the expat speaks Russian and needs BOTH
        #    the Spanish to say out loud AND the English to check they got it
        #    right. Mirrors whatsapp_convo_mode.process_convo_message().
        produced = []
        if detected_lang == "ru":
            es_text = _convo_translate(transcription, "ru", "es")
            en_text = _convo_translate(transcription, "ru", "en")
            if not es_text or not en_text:
                bot.reply_to(message, "❌ Translation error. Try again?")
                return

            bot.send_message(
                chat_id,
                f"🎤 *{transcription}*\n\n🇪🇸 {es_text}\n\n🇬🇧 {en_text}",
                parse_mode="Markdown",
            )

            # Distinct slot ids per clip — a shared id makes the second render
            # overwrite the first (see _convo_voice_note).
            for clip_text, clip_lang, slot in (
                (es_text, "es", message.message_id * 2),
                (en_text, "en", message.message_id * 2 + 1),
            ):
                path = _convo_voice_note(clip_text, clip_lang, slot)
                if path and os.path.exists(path):
                    with open(path, "rb") as voice:
                        bot.send_voice(chat_id, voice, timeout=180)
                    produced.append(path)

            print(f"CONVO ACTION user={user_id} ru->es+en voices={len(produced)}", flush=True)
        else:
            target_lang = conversation_mode.get_target_language(user_id)
            translate_to = get_opposite_language(detected_lang, target_lang)
            # Never echo the speaker back to themselves.
            if translate_to == detected_lang:
                translate_to = "en" if detected_lang == "es" else "es"

            translation = _convo_translate(transcription, detected_lang, translate_to)
            if not translation:
                bot.reply_to(message, "❌ Translation error. Try again?")
                return

            lang_flag = "🇪🇸" if translate_to == "es" else "🇬🇧"
            bot.send_message(
                chat_id,
                f"🎤 *{transcription}*\n{lang_flag} {translation}",
                parse_mode="Markdown",
            )

            path = _convo_voice_note(translation, translate_to, message.message_id * 2)
            if path and os.path.exists(path):
                with open(path, "rb") as voice:
                    bot.send_voice(chat_id, voice, timeout=180)
                produced.append(path)

            print(
                f"CONVO ACTION user={user_id} {detected_lang}->{translate_to} voices={len(produced)}",
                flush=True,
            )

        # Track usage
        conversation_mode.increment_count(user_id)

        # Cleanup
        for f in [temp_ogg, temp_mp3] + produced:
            if os.path.exists(f):
                os.remove(f)
                
    except Exception as e:
        print(f"Conversation mode error: {e}")
        bot.reply_to(message, f"❌ Translation error. Try again?")


@bot.message_handler(commands=["subscribe"])
def handle_subscribe(message):
    """Show subscription options"""
    user_id = str(message.from_user.id)
    
    # Check trial status if PayPal system available
    trial_info = ""
    if PAYPAL_SYSTEM_AVAILABLE and paypal_system:
        trial_status = paypal_system.get_trial_status(user_id)
        if trial_status["has_trial"]:
            if trial_status["is_active"]:
                days = trial_status["days_remaining"]
                trial_info = f"\n✅ You have {days} days left in your free trial!\n"
            else:
                trial_info = "\n⏰ Your free trial has expired.\n"
        else:
            trial_info = "\n🎉 Start your 14-day free trial now!\n"
    
    sub_msg = f"""💳 EspaLuz Subscription
{trial_info}
🎯 Simple Pricing:
• ${PAGUELOFACIL_AMOUNT if PAGUELOFACIL_AVAILABLE else '11'}/month — full access, family included
• 14-day FREE trial included!

🇵🇦 **Panamá / tarjeta local:** /pagar — pago único con PagueloFacil (Visa, Mastercard, PagoCash)
💳 **PayPal** (suscripción mensual):
{PAYPAL_SUBSCRIPTION_LINK}

🔑 After PayPal subscribe:
Send me your Subscription ID (I-XXXXXXXXXXXX) to activate instantly!
Find it in your PayPal confirmation or Settings → Payments → Automatic payments

✨ Your Spanish learning journey awaits!"""
    
    bot.send_message(message.chat.id, sub_msg)


@bot.message_handler(commands=["pagar", "pay"])
def handle_pagar(message):
    """Generate PagueloFacil one-time payment link (Panama / LATAM cards)."""
    user_id = str(message.from_user.id)

    if not paguelofacil_system:
        bot.reply_to(
            message,
            "⚠️ PagueloFacil no está disponible aún.\n"
            f"Usa PayPal: {PAYPAL_SUBSCRIPTION_LINK}",
        )
        return

    if not PAGUELOFACIL_AVAILABLE:
        bot.reply_to(
            message,
            "⚠️ PagueloFacil aún no está activado en el servidor.\n"
            "Estamos esperando el código CCLW del comercio.\n\n"
            f"Mientras tanto, PayPal: {PAYPAL_SUBSCRIPTION_LINK}",
        )
        return

    access = paguelofacil_system.get_access_info(user_id)
    if access.get("active"):
        bot.reply_to(
            message,
            f"✅ Ya tienes acceso activo hasta {access['paid_until']} ({access['days_remaining']} días).\n"
            "You already have active access.\n\n"
            "Para renovar antes de que expire, usa /pagar de nuevo.",
        )
        return

    bot.reply_to(message, "🔗 Generando enlace de pago seguro… / Creating secure payment link…")
    result = paguelofacil_system.create_payment_link(user_id)

    if not result.get("success"):
        bot.send_message(
            message.chat.id,
            f"❌ No pude crear el enlace: {result.get('error', 'error desconocido')}\n\n"
            f"Prueba PayPal: {PAYPAL_SUBSCRIPTION_LINK}",
        )
        return

    url = result["url"]
    amount = result.get("amount", PAGUELOFACIL_AMOUNT)
    bot.send_message(
        message.chat.id,
        f"""💳 **Pago único EspaLuz — ${amount}**

🇵🇦 PagueloFacil (tarjeta Visa/Mastercard o PagoCash en Panamá)

👉 {url}

• Acceso: **30 días** completos
• Tras pagar, **no necesitas /link** — te confirmamos aquí automáticamente
• El enlace expira en 1 hora

¿Problemas? Escríbenos o usa PayPal: {PAYPAL_SUBSCRIPTION_LINK}""",
        disable_web_page_preview=False,
    )


@bot.message_handler(commands=["trial"])
def handle_trial(message):
    """Check or start trial status"""
    user_id = str(message.from_user.id)
    
    if not PAYPAL_SYSTEM_AVAILABLE or not paypal_system:
        bot.reply_to(message, "🎉 You have full access! Enjoy EspaLuz!")
        return
    
    trial_status = paypal_system.get_trial_status(user_id)
    
    if not trial_status["has_trial"]:
        # Start trial for new user
        paypal_system.start_trial(user_id)
        bot.reply_to(message, """🎉 Welcome to EspaLuz!

Your 14-day FREE TRIAL has started!

What you can do:
• 🎤 Send voice messages for practice
• 📷 Take photos of text to translate
• 💬 Chat in Spanish or English
• 🌎 Learn about your new country

Try sending me a message or voice note!

/help - See all commands
/menu - Full feature list""")
    
    elif trial_status["is_active"]:
        days = trial_status["days_remaining"]
        messages = trial_status["messages_sent"]
        org = trial_status.get("org_code")
        org_text = f"\n🏢 Organization: {org}" if org else ""
        
        bot.reply_to(message, f"""✅ Trial Status

📅 Days remaining: {days}
💬 Messages sent: {messages}{org_text}

Keep practicing! 🚀
/subscribe - View subscription options""")
    
    else:
        bot.reply_to(message, f"""⏰ Trial Expired

Your free trial has ended.

To continue your Spanish learning journey:
💳 Subscribe: {PAYPAL_SUBSCRIPTION_LINK}

🔑 After subscribing, send me your Subscription ID (I-XXXX)!""")


@bot.message_handler(commands=["admin"])
def handle_admin(message):
    """Admin command - show admin dashboard info"""
    user_id = str(message.from_user.id)
    
    # Only allow admin access for specific users
    ADMIN_IDS = ["1494063516", "YOUR_ADMIN_ID"]  # Add your Telegram ID
    
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "⚠️ Admin access required.")
        return
    
    if PAYPAL_SYSTEM_AVAILABLE and paypal_system:
        stats = paypal_system.get_stats()
        admin_msg = f"""🎯 EspaLuz Admin Stats

👥 Total Users: {stats['total_users']}
✅ Active Trials: {stats['active_trials']}
⏰ Expired Trials: {stats['expired_trials']}
💳 Active Subscriptions: {stats['active_subscriptions']}

🌐 Web Admin (if deployed):
https://your-deployment-url/admin

Commands:
/extend [user_id] [days] - Extend trial
/adduser [email] - Add subscriber
/addsub [subscription_id] - Add PayPal subscription"""
        bot.reply_to(message, admin_msg)
    else:
        bot.reply_to(message, "⚠️ PayPal system not initialized.")


@bot.message_handler(commands=["addsub"])
def handle_addsub(message):
    """Admin command to manually add a PayPal subscription ID for verification"""
    user_id = str(message.from_user.id)
    ADMIN_IDS = ["1494063516", "YOUR_ADMIN_ID"]
    
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "⚠️ Admin access required.")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, """Usage: /addsub I-XXXXXXXXXX

Find subscription ID in PayPal:
1. PayPal IPN History → Click message
2. Find 'recurring_payment_id' = I-XXXXXXXXXX
3. /addsub I-XXXXXXXXXX""")
        return
    
    subscription_id = parts[1].strip()
    
    if not subscription_id.startswith("I-"):
        bot.reply_to(message, "⚠️ Invalid format. Subscription ID should start with 'I-'")
        return
    
    bot.reply_to(message, f"🔍 Verifying subscription {subscription_id}...")
    
    if PAYPAL_SYSTEM_AVAILABLE and paypal_system:
        # Use the manual add function
        result = paypal_system.add_subscription_manually("", subscription_id)
        
        if result.get("success"):
            bot.send_message(message.chat.id, f"""✅ Subscription added successfully!

📧 Email: {result.get('email')}
🔑 Subscription ID: {result.get('subscription_id')}
📊 Status: {result.get('status')}

User can now link with: {result.get('email')}""")
        else:
            bot.send_message(message.chat.id, f"❌ Failed: {result.get('error')}")
    else:
        bot.reply_to(message, "⚠️ PayPal system not initialized.")


@bot.message_handler(func=lambda m: m.text and m.text.strip().upper().startswith("I-") and len(m.text.strip()) >= 10 and " " not in m.text.strip())
def handle_subscription_id(message):
    """Handle direct subscription ID verification - REAL PayPal API check"""
    subscription_id = message.text.strip().upper()
    user_id = str(message.from_user.id)
    
    print(f"🔑 Verifying subscription ID: {subscription_id} for user {user_id}")
    
    if PAYPAL_SYSTEM_AVAILABLE and paypal_system:
        result = paypal_system.verify_subscription_id_direct(user_id, subscription_id)
        bot.send_message(message.chat.id, result["message"])
        
        # === DATABASE: Record subscription if verified (NEW) ===
        if result.get("success") and DATABASE_AVAILABLE and db:
            try:
                # Extract email from result message
                import re
                email_match = re.search(r'Email: (\S+@\S+)', result.get("message", ""))
                email = email_match.group(1) if email_match else "unknown"
                db.record_subscription(user_id, email, subscription_id, "P-6GR95409C95293139NFSBJJY", "direct_id")
                print(f"📊 DB: Recorded subscription for {user_id}")
            except Exception as e:
                print(f"⚠️ DB subscription tracking error (non-fatal): {e}")
    else:
        bot.reply_to(message, "⚠️ PayPal system not available. Try again later.")


@bot.message_handler(func=lambda m: m.text and "@" in m.text and "." in m.text and " " not in m.text.strip())
def handle_email_link(message):
    """Handle email linking for PayPal subscriptions"""
    user_email = message.text.strip().lower()
    user_id = str(message.from_user.id)

    # Use new PayPal system if available
    if PAYPAL_SYSTEM_AVAILABLE and paypal_system:
        result = paypal_system.link_email(user_id, user_email)
        bot.send_message(message.chat.id, result["message"])
        return

    # Fallback to legacy system
    try:
        subscribers_file = "subscribers.json"
        if os.path.exists(subscribers_file):
            with open(subscribers_file, "r+") as f:
                data = json.load(f)
                if user_email in data:
                    data[user_email]["telegram_id"] = user_id
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()
                    bot.send_message(message.chat.id, "✅ Email linked! You now have full access to Espaluz.")
                else:
                    bot.send_message(message.chat.id, f"⚠️ Email not found. Subscribe first:\n{PAYPAL_SUBSCRIPTION_LINK}")
        else:
            bot.send_message(message.chat.id, f"⚠️ No subscribers file found. Subscribe first:\n{PAYPAL_SUBSCRIPTION_LINK}")
    except Exception as e:
        print(f"❌ Error linking email: {e}")
        bot.send_message(message.chat.id, "⚠️ Something went wrong. Please try again.")


# =============================================================================
# 🎙️ CONVERSATION MODE - Real-time voice translation (NEW - Jan 2026)
# =============================================================================

# Track which users are in conversation mode
conversation_mode_users = {}

def detect_language(text):
    """Detect language of input text (simple heuristic + can use Claude for accuracy)"""
    # Russian characters
    if any('\u0400' <= char <= '\u04FF' for char in text):
        return 'ru'
    
    # Spanish-specific patterns
    spanish_markers = ['¿', '¡', 'ñ', 'á', 'é', 'í', 'ó', 'ú']
    spanish_words = ['el', 'la', 'los', 'las', 'un', 'una', 'que', 'de', 'en', 'es', 'por', 'para', 'como', 'pero', 'más', 'este', 'esto', 'esta', 'ese', 'eso', 'esa', 'yo', 'tú', 'él', 'ella', 'nosotros', 'ustedes', 'ellos', 'hola', 'gracias', 'buenos', 'buenas']
    
    text_lower = text.lower()
    spanish_score = sum(1 for marker in spanish_markers if marker in text)
    spanish_score += sum(1 for word in spanish_words if f' {word} ' in f' {text_lower} ' or text_lower.startswith(f'{word} ') or text_lower.endswith(f' {word}'))
    
    # English patterns
    english_words = ['the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'hello', 'hi', 'thanks', 'thank', 'please', 'yes', 'no', 'okay', 'ok']
    
    english_score = sum(1 for word in english_words if f' {word} ' in f' {text_lower} ' or text_lower.startswith(f'{word} ') or text_lower.endswith(f' {word}'))
    
    if spanish_score > english_score:
        return 'es'
    elif english_score > spanish_score:
        return 'en'
    else:
        # Default to English if unclear
        return 'en'

def quick_translate_for_convo(text, source_lang, target_lang):
    """Fast translation for conversation mode - minimal latency.

    Claude first (10s timeout, this is the low-latency path), then the same
    4-provider chain the rest of the bot falls back to.

    Fixed 2026-08-16: this was the LAST single-provider LLM call in the bot.
    One bad Anthropic minute — a 529, a stale model id, an expired key — and it
    returned None with no second attempt, which reaches a family as a voice note
    whose translation simply never arrives. Every other reply path already had a
    chain behind it; this one was missed.

    The model id was also hard-coded here while `CLAUDE_MODEL` (env-driven,
    CLAUDE_MODEL_NAME) was already in use everywhere else, so a model change
    would have fixed the whole bot except this function.
    """
    prompt = f"""Translate the following text from {source_lang} to {target_lang}.
ONLY output the translation, nothing else. No explanations, no quotes, just the translated text.

Text: {text}

Translation:"""

    try:
        from llm_chain import free_tier
        if free_tier():  # 30 Oct 2026: free mode = the fallback below answers, Claude not first
            raise Exception("MODEL_TIER=free")
        response = requests.post(
            "https://api.anthropic.com/v1/messages",  # tier-gated
            headers={
                "Content-Type": "application/json",
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            return result["content"][0]["text"].strip()
        print(f"Translation API error: {response.status_code}")
    except Exception as e:
        print(f"Quick translate error: {e}")

    try:
        from llm_chain import PROFILE_FALLBACK, complete

        translation, errors = complete(None, prompt, max_tokens=500,
                                       order=PROFILE_FALLBACK)
        if translation:
            print(f"✅ Quick-translate fallback OK {source_lang}->{target_lang}", flush=True)
            return translation.strip()
        print(f"❌ Quick-translate fallback exhausted: {'; '.join(errors)[:200]}", flush=True)
    except Exception as chain_err:
        print(f"❌ Quick-translate fallback chain error: {chain_err}", flush=True)

    return None

def generate_voice_note(text, lang='es'):
    """Generate a voice note file for Telegram"""
    try:
        # Use gTTS for voice generation
        tts = gTTS(text=text, lang=lang, slow=False)
        timestamp = int(time.time() * 1000)
        filename = f"convo_voice_{timestamp}.mp3"
        tts.save(filename)
        return filename
    except Exception as e:
        print(f"Voice generation error: {e}")
        return None

# DEAD CODE — DELIBERATELY NOT REGISTERED. The live /convo handler is
# handle_convo() earlier in this file. telebot dispatches to the FIRST matching
# handler, so this second registration never fired and its state dict
# (conversation_mode_users) is therefore always empty. The decorator is removed
# so future fixes are not applied here by mistake.
def handle_convo_toggle(message):
    """Toggle conversation mode on/off (UNUSED — see handle_convo)"""
    user_id = str(message.from_user.id)
    
    # Parse command argument
    args = message.text.split()
    if len(args) > 1:
        arg = args[1].lower()
        if arg in ['on', 'start', 'begin', '1']:
            conversation_mode_users[user_id] = {
                'active': True,
                'target_lang': 'es',  # Default: translate TO Spanish
                'started': datetime.now().isoformat()
            }
            bot.send_message(message.chat.id, """🎙️ **CONVERSATION MODE ACTIVATED**

How it works:
1. Send a voice message in ANY language
2. I'll translate and speak back in the OTHER language

🇬🇧 English → 🇪🇸 Spanish
🇪🇸 Spanish → 🇬🇧 English  
🇷🇺 Russian → 🇪🇸 Spanish

Perfect for:
• Pharmacy visits
• Doctor appointments
• Parent-teacher meetings
• Shopping
• Any real conversation!

Send /convo off to exit.
Send /convo es to translate TO Spanish (default)
Send /convo en to translate TO English

🎤 Start speaking now!""")
            return
            
        elif arg in ['off', 'stop', 'end', '0']:
            if user_id in conversation_mode_users:
                del conversation_mode_users[user_id]
            bot.send_message(message.chat.id, "🔇 Conversation mode OFF. Back to normal tutor mode!")
            return
            
        elif arg == 'es':
            if user_id in conversation_mode_users:
                conversation_mode_users[user_id]['target_lang'] = 'es'
            else:
                conversation_mode_users[user_id] = {'active': True, 'target_lang': 'es', 'started': datetime.now().isoformat()}
            bot.send_message(message.chat.id, "🇪🇸 Target language set to SPANISH. I'll translate everything to Spanish.")
            return
            
        elif arg == 'en':
            if user_id in conversation_mode_users:
                conversation_mode_users[user_id]['target_lang'] = 'en'
            else:
                conversation_mode_users[user_id] = {'active': True, 'target_lang': 'en', 'started': datetime.now().isoformat()}
            bot.send_message(message.chat.id, "🇬🇧 Target language set to ENGLISH. I'll translate everything to English.")
            return
    
    # No argument - show current status
    if user_id in conversation_mode_users and conversation_mode_users[user_id].get('active'):
        target = conversation_mode_users[user_id].get('target_lang', 'es')
        target_name = 'Spanish' if target == 'es' else 'English'
        bot.send_message(message.chat.id, f"""🎙️ Conversation mode is ON
Target language: {target_name}

Commands:
/convo off - Turn off
/convo es - Translate to Spanish
/convo en - Translate to English""")
    else:
        bot.send_message(message.chat.id, """🎙️ Conversation mode is OFF

/convo on - Activate real-time voice translation
/convo es - Activate & translate to Spanish
/convo en - Activate & translate to English""")

def is_in_conversation_mode(user_id):
    """Check if user is in conversation mode"""
    return user_id in conversation_mode_users and conversation_mode_users[user_id].get('active', False)

def process_conversation_mode_voice(message, transcription):
    """Process voice message in conversation mode - fast translation + voice response"""
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    
    try:
        # Get user's target language
        target_lang = conversation_mode_users.get(user_id, {}).get('target_lang', 'es')
        
        # Detect source language
        source_lang = detect_language(transcription)
        source_name = {'en': 'English', 'es': 'Spanish', 'ru': 'Russian'}.get(source_lang, 'Unknown')
        target_name = {'en': 'English', 'es': 'Spanish'}.get(target_lang, 'Spanish')
        
        print(f"🎙️ CONVO MODE: {source_name} → {target_name}")
        
        # If source and target are the same, flip target
        if source_lang == target_lang:
            target_lang = 'en' if target_lang == 'es' else 'es'
            target_name = {'en': 'English', 'es': 'Spanish'}.get(target_lang, 'Spanish')
        
        # Send processing indicator
        bot.send_message(chat_id, f"🎙️ {source_name} → {target_name}...")
        
        # Quick translate
        translation = quick_translate_for_convo(transcription, source_lang, target_lang)
        
        if not translation:
            bot.send_message(chat_id, "❌ Translation failed. Try again.")
            return
        
        # Send text translation
        bot.send_message(chat_id, f"📝 {translation}")
        
        # Generate and send voice note
        voice_file = generate_voice_note(translation, target_lang)
        
        if voice_file and os.path.exists(voice_file):
            with open(voice_file, 'rb') as audio:
                bot.send_voice(chat_id, audio, timeout=180)
            os.remove(voice_file)
            print(f"✅ CONVO MODE: Voice sent successfully")
        else:
            print(f"⚠️ CONVO MODE: Could not generate voice")
            
    except Exception as e:
        print(f"❌ CONVO MODE error: {e}")
        bot.send_message(chat_id, f"❌ Error: {e}")


@bot.message_handler(content_types=["voice"])
def handle_voice(message):
    user_id = str(message.from_user.id)
    
    # === CONVERSATION MODE CHECK ===
    # If conversation mode is active, use fast translation instead of full tutor mode.
    # The access gate and usage tracking run FIRST: convo mode is a paid feature like
    # any other, and it must appear in daily_metrics. enforce_learning_access covers
    # BOTH rails — PayPal subscription and PagueloFacil prepaid — plus the trial.
    if conversation_mode.is_active(user_id):
        if not enforce_learning_access(message, user_id):
            return
        if DATABASE_AVAILABLE and db:
            try:
                db.track_user(
                    user_id,
                    username=message.from_user.username if message.from_user else None,
                    first_name=message.from_user.first_name if message.from_user else None,
                )
                db.track_message(user_id, 'voice')
                print(f"DB: Tracked convo voice from {user_id}", flush=True)
            except Exception as e:
                print(f"DB convo voice tracking error: {e}", flush=True)
        handle_conversation_voice(message)
        return

    # Track activity for analytics
    if ENHANCED_BRAIN_AVAILABLE:
        try:
            track_activity(user_id)
        except:
            pass
    
    # === DATABASE TRACKING ===
    if DATABASE_AVAILABLE and db:
        try:
            username = message.from_user.username if message.from_user else None
            first_name = message.from_user.first_name if message.from_user else None
            db.track_user(user_id, username=username, first_name=first_name)
            db.track_message(user_id, 'voice')
            print(f"DB: Tracked voice from {user_id}", flush=True)
        except Exception as e:
            print(f"DB voice tracking error: {e}", flush=True)
    
    if not enforce_learning_access(message, user_id):
        return

    try:
        file_info = bot.get_file(message.voice.file_id)
        voice_file = bot.download_file(file_info.file_path)

        temp_ogg_path = f"input_{message.message_id}.ogg"
        temp_mp3_path = f"input_{message.message_id}.mp3"

        with open(temp_ogg_path, "wb") as f:
            f.write(voice_file)

        subprocess.run(["ffmpeg", "-i", temp_ogg_path, temp_mp3_path], check=True)

        transcription = transcribe_audio(temp_mp3_path, whisper_hint(user_sessions.get(str(user_id))))

        if not transcription:
            bot.reply_to(message, "❌ No pude transcribir este mensaje de voz. / I couldn't transcribe this voice message.")
            return

        print(f"📝 Voice transcription: {transcription}")
        
        # === CHECK FOR CONVERSATION MODE ===
        if is_in_conversation_mode(user_id):
            print(f"🎙️ User {user_id} is in CONVERSATION MODE")
            process_conversation_mode_voice(message, transcription)
            # Clean up
            os.remove(temp_ogg_path)
            os.remove(temp_mp3_path)
            return
        
        # === NORMAL TUTOR MODE ===
        _kid = (user_sessions.get(str(user_id), {}).get("context", {}).get("user", {})
                .get("preferences", {}).get("family_role") == "alisa")
        bot.send_message(message.chat.id, f"🎤 Alisa dijo / Alisa said:\n{transcription}" if _kid
                         else f"🗣️ Transcripción:\n{transcription}")

        process_message_with_tracking(transcription, message.chat.id, str(message.from_user.id), message)

        os.remove(temp_ogg_path)
        os.remove(temp_mp3_path)

    except Exception as e:
        print(f"❌ Error processing voice message: {e}")
        bot.reply_to(message, "❌ Hubo un error al procesar tu mensaje de voz.")

@bot.message_handler(content_types=["text"])
def handle_text(message):
    print(f">>> HANDLE_TEXT ENTERED: {message.from_user.id} - {message.text[:30] if message.text else 'None'}", flush=True)
    user_id = str(message.from_user.id)
    text = message.text.strip()
    
    # === DATABASE TRACKING (first thing!) ===
    if DATABASE_AVAILABLE and db:
        try:
            username = message.from_user.username if message.from_user else None
            first_name = message.from_user.first_name if message.from_user else None
            db.track_user(user_id, username=username, first_name=first_name)
            db.track_message(user_id, 'text')
            print(f"DB: Tracked text from {user_id}", flush=True)
        except Exception as e:
            print(f"DB tracking error: {e}", flush=True)
    
    # Track activity for analytics
    if ENHANCED_BRAIN_AVAILABLE:
        try:
            track_activity(user_id)
        except:
            pass

    if not enforce_learning_access(message, user_id):
        return

    # === ONBOARDING FLOW ===
    onboarding = get_user_onboarding(user_id)
    current_step = onboarding.get("step", "country")
    
    if current_step != "complete":
        # User is in onboarding mode
        
        if current_step == "country":
            # Try to detect country from message
            country = detect_country_from_text(text)
            if country:
                onboarding["country"] = country
                onboarding["step"] = "name"
                set_user_onboarding(user_id, onboarding)
                bot.send_message(message.chat.id, ONBOARDING_MESSAGES["name"])
            else:
                # Couldn't detect country, ask again
                bot.send_message(message.chat.id, 
                    f"🤔 I didn't recognize '{text}' as a country.\n\n"
                    "Please type a country name like:\n"
                    "• Panama\n• Mexico\n• Colombia\n• Spain\n• Costa Rica\n• USA\n\n"
                    "Or any other Spanish-speaking country!")
            return
        
        elif current_step == "name":
            # Accept any text as name
            name = text.split()[0].capitalize()  # Take first word as name
            onboarding["name"] = name
            onboarding["step"] = "role"
            set_user_onboarding(user_id, onboarding)
            msg = ONBOARDING_MESSAGES["role"].format(name=name)
            bot.send_message(message.chat.id, msg)
            return
        
        elif current_step == "role":
            # Try to detect role from message
            role = detect_role_from_text(text)
            if not role:
                # Default to traveler if can't detect
                role = "traveler"
            
            onboarding["role"] = role
            
            # If parent or expat, ask about family
            if role in ["parent", "expat"]:
                onboarding["step"] = "family_spouse"
                set_user_onboarding(user_id, onboarding)
                msg = ONBOARDING_MESSAGES["family_spouse"].format(name=onboarding.get("name", "Friend"))
                bot.send_message(message.chat.id, msg)
            else:
                # Skip family questions for non-parents
                onboarding["step"] = "complete"
                set_user_onboarding(user_id, onboarding)
                finish_onboarding(user_id, message, onboarding)
            return
        
        elif current_step == "family_spouse":
            # Parse spouse info
            text_lower = text.lower()
            if "skip" in text_lower:
                onboarding["spouse"] = None
            elif "single" in text_lower:
                onboarding["spouse"] = "single parent"
            else:
                # Try to extract spouse name
                onboarding["spouse"] = text.strip()
            
            onboarding["step"] = "family_children"
            set_user_onboarding(user_id, onboarding)
            bot.send_message(message.chat.id, ONBOARDING_MESSAGES["family_children"])
            return
        
        elif current_step == "family_children":
            # Parse children info
            text_lower = text.lower()
            if "skip" in text_lower or "no children" in text_lower or "no kids" in text_lower:
                onboarding["children"] = []
            else:
                # Store raw children info - will be parsed later
                onboarding["children_raw"] = text.strip()
                # Try to parse children: "Alisa 4, Marco 8"
                children = []
                import re
                # Match patterns like "Alisa 4" or "Sofia, 8" or "Marco 5 years"
                patterns = re.findall(r'([A-Za-zА-Яа-я]+)\s*,?\s*(\d+)', text)
                for name, age in patterns:
                    children.append({"name": name.capitalize(), "age": int(age)})
                onboarding["children"] = children
            
            onboarding["step"] = "complete"
            set_user_onboarding(user_id, onboarding)
            
            # Build family summary
            family_summary = ""
            if onboarding.get("spouse"):
                family_summary += f"💑 {onboarding['spouse']}\n"
            if onboarding.get("children"):
                for child in onboarding["children"]:
                    family_summary += f"👶 {child['name']} ({child['age']} years old)\n"
            
            if family_summary:
                bot.send_message(message.chat.id, 
                    ONBOARDING_MESSAGES["family_complete"].format(family_summary=family_summary))
            
            finish_onboarding(user_id, message, onboarding)
            return
    
    # === NORMAL CONVERSATION (onboarding complete) ===
    process_message_with_tracking(message.text, message.chat.id, str(message.from_user.id), message)

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    """Handle photo message with text recognition and explanation for Telegram"""
    try:
        user_id = str(message.from_user.id)
        print(f"[INFO] Received photo from user {user_id} at {message.date}", flush=True)
        
        # === DATABASE TRACKING ===
        if DATABASE_AVAILABLE and db:
            try:
                username = message.from_user.username if message.from_user else None
                first_name = message.from_user.first_name if message.from_user else None
                db.track_user(user_id, username=username, first_name=first_name)
                db.track_message(user_id, 'image')
                print(f"DB: Tracked photo from {user_id}", flush=True)
            except Exception as e:
                print(f"DB photo tracking error: {e}", flush=True)

        if not enforce_learning_access(message, user_id):
            return

        # Kids mode (30 Oct 2026): her toy, drawing or lunch is not a text to read - Pere and Titi look at it and talk
        # about it in the normal lesson flow (same path as her voice notes), so the photo becomes today's sentence.
        _prefs = user_sessions.get(user_id, {}).get("context", {}).get("user", {}).get("preferences", {})
        if _prefs.get("family_role") == "alisa":
            bot.send_message(message.chat.id, "👀 Pere y Titi miran tu foto... / Pere and Titi are looking at your photo...")
            seen = kids_photo_story(bot.download_file(bot.get_file(message.photo[-1].file_id).file_path))
            if not seen:
                bot.send_message(message.chat.id, "🦥 No pude ver bien tu foto. ¿Me cuentas qué es? / I could not see your photo well. Can you tell me what it is?")
                return
            caption = (message.caption or "").strip()
            said = f"[Alisa sent a photo{' and wrote: ' + caption if caption else ''}] The photo shows: {seen}"
            process_message_with_tracking(said, message.chat.id, user_id, message)
            return

        # Step 1: Send initial processing message
        processing_msg = bot.send_message(message.chat.id, "🔍 Procesando imagen... / Processing image...")
        print(f"[INFO] Sent processing message (ID: {processing_msg.message_id})", flush=True)

        # Step 2: Download the photo
        try:
            file_id = message.photo[-1].file_id
            print(f"[INFO] Downloading photo with file_id: {file_id}", flush=True)
            file_info = bot.get_file(file_id)
            photo_file = bot.download_file(file_info.file_path)
            print("[INFO] Photo downloaded successfully", flush=True)
        except Exception as e:
            error_msg = f"❌ Error descargando la foto: {str(e)} / Error downloading photo: {str(e)}"
            bot.edit_message_text(error_msg, chat_id=message.chat.id, message_id=processing_msg.message_id)
            print(f"[ERROR] Photo download failed: {str(e)}", flush=True)
            return

        # Step 3: Update to analyzing status
        bot.edit_message_text("🔍 Analizando texto... / Analyzing text...", chat_id=message.chat.id, message_id=processing_msg.message_id)
        print("[INFO] Updated to analyzing status", flush=True)

        # Step 4: Extract text using process_photo
        try:
            print("[INFO] Extracting text with process_photo", flush=True)
            result = process_photo(photo_file)
            if not result or "Error processing image" in result or "No text found" in result:
                error_msg = f"❌ {result or 'No se detectó texto en la imagen. / No text detected in the image.'}"
                bot.edit_message_text(error_msg, chat_id=message.chat.id, message_id=processing_msg.message_id)
                print(f"[ERROR] Text extraction failed: {error_msg}", flush=True)
                return
            print("[INFO] Text extracted successfully", flush=True)
        except Exception as e:
            error_msg = f"❌ Error procesando la imagen: {str(e)} / Error processing image: {str(e)}"
            bot.edit_message_text(error_msg, chat_id=message.chat.id, message_id=processing_msg.message_id)
            print(f"[ERROR] Text extraction error: {str(e)}", flush=True)
            return

        # Step 5: Chunk and send extracted text
        try:
            extracted_text = result.split("\n\n", 1)[1] if "\n\n" in result else result
            word_count = len(extracted_text.split())
            print(f"[INFO] Extracted {word_count} words, preparing to send", flush=True)
            MAX_LENGTH = 4000
            intro = f"📷 Resultado / Result ({word_count} palabras/words):\n\n"
            chunks = []
            current_chunk = ""
            paragraphs = extracted_text.split("\n\n")

            for para in paragraphs:
                test_chunk = ("" if not current_chunk else "\n\n") + para
                if len(current_chunk) + len(test_chunk) <= MAX_LENGTH - len(intro if not chunks else ""):
                    current_chunk += test_chunk
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = para

            if current_chunk:
                chunks.append(current_chunk)

            for i, chunk in enumerate(chunks, 1):
                chunk_msg = f"{intro if i == 1 else ''}Parte {i}/{len(chunks)}:\n\n{chunk}"
                bot.send_message(message.chat.id, chunk_msg)
                print(f"[INFO] Sent text chunk {i}/{len(chunks)}, length: {len(chunk_msg)}", flush=True)
                time.sleep(0.5)

            bot.delete_message(message.chat.id, processing_msg.message_id)
            print("[INFO] Deleted processing message", flush=True)

        except Exception as e:
            error_msg = f"❌ Error enviando el resultado: {str(e)} / Error sending result: {str(e)}"
            bot.edit_message_text(error_msg, chat_id=message.chat.id, message_id=processing_msg.message_id)
            print(f"[ERROR] Failed to send text chunks: {str(e)}", flush=True)
            return

        # Step 6: Update learning data
        family_member = None  # Initialize default
        try:
            if user_id in user_sessions:
                family_member = user_sessions[user_id].get("context", {}).get("user", {}).get("preferences", {}).get("family_role", None)
                print(f"[INFO] Found family_member: {family_member}", flush=True)
                learned_items = identify_language_learning_content(extracted_text, family_member)
                user_sessions[user_id] = update_session_learning(user_sessions[user_id], learned_items)
                print("[INFO] Updated learning data for user", flush=True)
            else:
                print("[WARN] No session found for user_id, skipping learning update", flush=True)
        except Exception as e:
            print(f"[WARN] Failed to update learning data: {str(e)}", flush=True)

        # Step 7: Get educational explanation from Claude
        try:
            explanation_prompt = f"""
The user sent a photo with text, and I extracted the following information:

{extracted_text}

Please provide a brief educational explanation about this text that could be helpful for a Russian expat in Panama. 
- Focus on key cultural context, vocabulary insights, or practical usage tips that would help them understand and remember this content.
- Keep your response concise and helpful.
- Avoid including any video script sections.
"""
            print(f"[INFO] Preparing Claude explanation prompt, length: {len(explanation_prompt)}", flush=True)

            if user_id not in user_sessions:
                user_sessions[user_id] = create_initial_session(user_id, message.from_user, message.chat, extracted_text)
                print(f"[INFO] Created new session for user {user_id}", flush=True)

            session = user_sessions[user_id]
            session["messages"].append({"role": "user", "content": explanation_prompt})

            print("[INFO] Calling ask_claude_with_mcp", flush=True)
            try:
                full_reply, short_reply, thinking_process = ask_claude_with_mcp(session, None)
                print(f"[INFO] Claude responded, full_reply length: {len(full_reply)}", flush=True)
            except Exception as claude_error:
                error_msg = f"❌ Error al consultar Claude: {str(claude_error)} / Error querying Claude: {str(claude_error)}"
                bot.send_message(message.chat.id, error_msg)
                print(f"[ERROR] Claude API call failed: {str(claude_error)}", flush=True)
                return

            if not full_reply or not full_reply.strip():
                error_msg = "⚠️ Claude devolvió una respuesta vacía. Intenta de nuevo. / Claude returned an empty response. Try again."
                bot.send_message(message.chat.id, error_msg)
                print("[ERROR] Claude returned empty response", flush=True)
                return

            full_reply_cleaned = re.sub(r"\[VIDEO SCRIPT START\](.*?)\[VIDEO SCRIPT END\]", "", full_reply, flags=re.DOTALL).strip()
            full_reply_cleaned = strip_shot_tags(full_reply_cleaned)
            print(f"[INFO] Cleaned explanation length: {len(full_reply_cleaned)}", flush=True)

            if not full_reply_cleaned:
                error_msg = "⚠️ La explicación estaba vacía después de procesar. Intenta de nuevo. / The explanation was empty after processing. Try again."
                bot.send_message(message.chat.id, error_msg)
                print("[ERROR] Cleaned explanation is empty", flush=True)
                return

            MAX_LENGTH = 3900
            intro = "💡 Explicación / Explanation:\n\n"
            explanation_chunks = []

            # Split long paragraphs into sentences if needed
            paragraphs = full_reply_cleaned.split("\n\n")
            refined_paragraphs = []
            for para in paragraphs:
                if len(para) > MAX_LENGTH - len(intro):
                    sentences = para.split(". ")
                    temp_para = ""
                    for sentence in sentences:
                        if len(temp_para) + len(sentence) + 2 <= MAX_LENGTH - len(intro):
                            temp_para += sentence + ". "
                        else:
                            if temp_para:
                                refined_paragraphs.append(temp_para.strip())
                            temp_para = sentence + ". "
                    if temp_para:
                        refined_paragraphs.append(temp_para.strip())
                else:
                    refined_paragraphs.append(para)

            current_chunk = ""
            for para in refined_paragraphs:
                test_chunk = ("" if not current_chunk else "\n\n") + para
                if len(current_chunk) + len(test_chunk) <= MAX_LENGTH - len(intro if not explanation_chunks else ""):
                    current_chunk += test_chunk
                else:
                    if current_chunk:
                        explanation_chunks.append(current_chunk)
                    current_chunk = para

            if current_chunk:
                explanation_chunks.append(current_chunk)

            if not explanation_chunks:
                error_msg = "⚠️ No se generó ninguna explicación válida. Intenta de nuevo. / No valid explanation was generated. Try again."
                bot.send_message(message.chat.id, error_msg)
                print("[ERROR] No explanation chunks generated", flush=True)
                return

            for i, chunk in enumerate(explanation_chunks, 1):
                chunk_msg = f"{intro if i == 1 else ''}Parte {i}/{len(explanation_chunks)}:\n\n{chunk}"
                try:
                    print(f"[INFO] Sending explanation chunk {i}/{len(explanation_chunks)}, length: {len(chunk_msg)}", flush=True)
                    bot.send_message(message.chat.id, chunk_msg)
                    time.sleep(1)
                except Exception as send_error:
                    error_msg = f"❌ Error enviando parte {i} de la explicación: {str(send_error)} / Error sending explanation part {i}: {str(send_error)}"
                    bot.send_message(message.chat.id, error_msg)
                    print(f"[ERROR] Failed to send explanation chunk {i}: {str(send_error)}", flush=True)
                    return

            session["messages"].append({"role": "assistant", "content": full_reply})
            # Update learning data for explanation
            try:
                # Re-fetch family_member to ensure it's defined
                family_member = session.get("context", {}).get("user", {}).get("preferences", {}).get("family_role", None)
                print(f"[INFO] Using family_member for explanation learning: {family_member}", flush=True)
                learned_items = enhance_language_learning_detection(full_reply_cleaned, family_member, session)
                user_sessions[user_id] = update_session_learning(user_sessions[user_id], learned_items)
                print("[INFO] Updated session with explanation learning data", flush=True)
            except Exception as learning_error:
                print(f"[WARN] Failed to update learning data for explanation: {str(learning_error)}", flush=True)

            print("[INFO] Explanation fully sent and session updated", flush=True)

        except Exception as e:
            error_msg = f"❌ Error obteniendo la explicación: {str(e)} / Error getting explanation: {str(e)}"
            bot.send_message(message.chat.id, error_msg)
            print(f"[ERROR] Explanation block failed: {str(e)}", flush=True)

    except Exception as e:
        try:
            error_msg = f"❌ Error general procesando la imagen: {str(e)} / General error processing image: {str(e)}"
            bot.send_message(message.chat.id, error_msg)
            print(f"[ERROR] General error in handle_photo: {str(e)}", flush=True)
        except Exception as send_error:
            print(f"[ERROR] Failed to send error message: {str(send_error)}", flush=True)

def debug_files_and_env():
    """Print debugging info about environment and files"""
    print("\n=== DEBUGGING INFO ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Available MP4 files: {[f for f in os.listdir('.') if f.endswith('.mp4')]}")
    print(f"FFmpeg available: {FFMPEG_AVAILABLE}")
    print(f"Python version: {subprocess.check_output(['python', '--version']).decode().strip()}")
    print(f"Disk free space: {subprocess.check_output(['df', '-h', '.']).decode().strip()}")
    print("====================\n")

print("✅ Espaluz is running THIS UPDATED VERSION: v4.0-paypal-demo-mode")

# Call the debug function here
debug_files_and_env()

from telebot.types import BotCommand
import threading
import os

# === Register custom bot commands ===
custom_commands = [
    BotCommand("start", "Welcome & quick start"),
    BotCommand("menu", "Full command menu"),
    BotCommand("help", "Help and instructions"),
    BotCommand("trial", "Check your free trial status"),
    BotCommand("pagar", "Pay $11 via PagueloFacil — 30 days access"),
    BotCommand("subscribe", "Payment options: PayPal & PagueloFacil"),
    BotCommand("link", "Link PayPal subscription ID (I-XXXX)"),
    BotCommand("convo", "Real-time voice translation mode"),
    BotCommand("progress", "Your learning progress"),
    BotCommand("profile", "View your profile"),
    BotCommand("reset", "Reset conversation"),
    BotCommand("family", "Switch family member"),
    BotCommand("kids", "Kids 6-7: Pere and Titi teach Spanish + English"),
    BotCommand("mama", "Back to adult mode after /kids"),
]

def register_commands_with_retry(max_retries=5, initial_delay=10):
    """Register bot commands with more aggressive exponential backoff"""
    for attempt in range(max_retries):
        try:
            # Exponential backoff with longer initial delay
            current_delay = initial_delay * (2 ** attempt)
            time.sleep(current_delay)

            bot.set_my_commands(custom_commands)
            print("✅ Bot commands registered successfully")
            return
        except Exception as e:
            print(f"Warning: Could not set commands (attempt {attempt + 1}/{max_retries}): {e}")
            if "Too Many Requests" in str(e):
                try:
                    # Extract retry time and add buffer
                    retry_after = int(str(e).split("retry after ")[1].split()[0])
                    time.sleep(retry_after + 5)
                except:
                    # Fallback if can't parse retry time
                    time.sleep(current_delay * 2)
    print("❌ Failed to register commands after all retries")

# Register commands with retry
register_commands_with_retry()

# DEAD CODE — DELIBERATELY NOT REGISTERED. A photo handler is already registered
# earlier in this file and telebot dispatches to the FIRST match, so this one
# never ran. Decorator removed so it cannot be mistaken for the live path.
def handle_photo_resilient_unused(message):
    """Handle photo message with text recognition and translation (UNUSED)"""
    try:
        # Step 1: Send processing message
        processing_msg = bot.send_message(message.chat.id, "🔍 Procesando imagen... / Processing image...")

        # Step 2: Download the photo - with error handling
        try:
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            photo_file = bot.download_file(file_info.file_path)
        except Exception as e:
            bot.edit_message_text(f"❌ Error downloading photo: {str(e)}",
                                  chat_id=message.chat.id,
                                  message_id=processing_msg.message_id)
            return

        # Step 3: Notify user we're analyzing
        bot.edit_message_text("🔍 Analizando texto... / Analyzing text...",
                              chat_id=message.chat.id,
                              message_id=processing_msg.message_id)

        # Step 4: Extract text from photo
        try:
            result = process_photo(photo_file)

            if not result or "Error processing image" in result or "No text found" in result:
                bot.edit_message_text(f"❌ {result or 'No se detectó texto en la imagen. / No text detected in the image.'}",
                                      chat_id=message.chat.id,
                                      message_id=processing_msg.message_id)
                return
        except Exception as e:
            bot.edit_message_text(f"❌ Error processing image: {str(e)}",
                                  chat_id=message.chat.id,
                                  message_id=processing_msg.message_id)
            return

        # Step 5: Show extracted translation result
        bot.edit_message_text("📷 Resultado / Result:\n\n" + result,
                              chat_id=message.chat.id,
                              message_id=processing_msg.message_id)

        # Step 6: Enhance learning
        try:
            user_id = str(message.from_user.id)
            if user_id in user_sessions:
                family_member = user_sessions[user_id]["context"]["user"]["preferences"]["family_role"]
                learned_items = identify_language_learning_content(result, family_member)
                user_sessions[user_id] = update_session_learning(user_sessions[user_id], learned_items)
        except Exception as e:
            print(f"Warning: Could not update learning data: {e}")

        # Step 7: Ask Claude for an explanation - with error handling
        try:
            explanation_prompt = f"""The user sent a photo with text, and I extracted the following information:

{result}

Please provide a brief educational explanation about this text that could be helpful for a Russian expat in Panama. 
Focus on any cultural context, vocabulary insights, or practical usage tips that would help them understand and remember this content.
Keep your response concise and helpful."""

            if user_id in user_sessions:
                session = user_sessions[user_id]
                session["messages"].append({"role": "user", "content": explanation_prompt})
                full_reply, short_reply, thinking_process = ask_claude_with_mcp(session, None)

                # 🧹 Remove [VIDEO SCRIPT] block safely
                full_reply_cleaned = re.sub(r"\[VIDEO SCRIPT START\](.*?)\[VIDEO SCRIPT END\]", "", full_reply, flags=re.DOTALL).strip()
                full_reply_cleaned = strip_shot_tags(full_reply_cleaned)

                # ✅ Safe chunking into 4096-character messages
                MAX_LENGTH = 4096
                intro = "💡 Explicación / Explanation:\n\n"
                chunks = []

                while full_reply_cleaned:
                    chunk = full_reply_cleaned[:MAX_LENGTH - len(intro if not chunks else "")]
                    split_at = chunk.rfind('\n')
                    if split_at == -1 or split_at < len(chunk) * 0.5:
                        split_at = chunk.rfind('.')
                    if split_at != -1:
                        chunk = chunk[:split_at + 1]
                    chunks.append((intro if not chunks else "") + chunk.strip())
                    full_reply_cleaned = full_reply_cleaned[len(chunk):].strip()

                for chunk in chunks:
                    bot.send_message(message.chat.id, chunk)

                # Save explanation
                session["messages"].append({"role": "assistant", "content": full_reply})
                learned_items = enhance_language_learning_detection(full_reply_cleaned, family_member, session)
                user_sessions[user_id] = update_session_learning(user_sessions[user_id], learned_items)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error getting explanation: {str(e)}")

    except Exception as e:
        try:
            bot.send_message(message.chat.id, f"❌ Error general procesando la imagen: {str(e)}")
        except:
            print(f"Failed to send error message: {e}")

print("✅ Espaluz is running THIS UPDATED VERSION: v4.0-paypal-demo-mode (Polling Mode)")

# DISABLED: Gumroad subscription poller - using PayPal now
# def run_subscription_poller():
#     from poll_subscriptions import fetch_all_subscribers, update_subscriber_file
#     while True:
#         try:
#             print(f"\n🔄 Polling Gumroad API inside bot runtime...")
#             subscribers = fetch_all_subscribers()
#             update_subscriber_file(subscribers)
#         except Exception as e:
#             print(f"❌ Subscription poller crashed: {e}")
#         time.sleep(300)
# threading.Thread(target=run_subscription_poller, daemon=True).start()
print("📌 Gumroad poller disabled - using PayPal subscriptions")

# === TEMP DEBUG: PRINT CURRENT SUBSCRIBERS TO LOGS ===
try:
    with open("subscribers.json", "r") as f:
        print("\n📄 subscribers.json:\n", f.read())
except Exception as e:
    print("❌ Could not read subscribers.json:", e)

# === Start the bot with polling mode ===
if __name__ == "__main__":
    while True:  # Add infinite retry loop
        try:
            print("🤖 Espaluz starting in polling mode...")
            
            # CRITICAL FIX: Ensure webhook is removed before polling
            try:
                print("Force removing webhook directly through API...")
                
                # Force delete
                delete_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook?drop_pending_updates=true"
                delete_response = requests.get(delete_url)
                print(f"Webhook deletion API response: {delete_response.json()}")
                
                # Verify webhook is gone
                info_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
                info_response = requests.get(info_url)
                webhook_info = info_response.json()
                print(f"Webhook info: {webhook_info}")
                
                # Wait to ensure changes propagate
                time.sleep(5)
                
                # Check again to really make sure
                info_response = requests.get(info_url)
                webhook_info = info_response.json()
                print(f"Webhook verification after waiting: {webhook_info}")
                
            except Exception as e:
                print(f"❌ ERROR during webhook removal: {e}")
            
            # Start polling
            print("📡 Starting polling with optimized settings...")
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=30,
                allowed_updates=["message", "edited_message", "callback_query"],
                interval=1,
                skip_pending=True
            )
        except Exception as e:
            print(f"❌ Bot critical error: {e}")
            import traceback
            traceback.print_exc()
            print("🔄 Attempting restart in 60 seconds...")
            time.sleep(60)  # Wait before retrying
