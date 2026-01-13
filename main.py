import os
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
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL_NAME", "claude-sonnet-4-20250514")
CLAUDE_API_VERSION = os.environ.get("CLAUDE_API_VERSION", "2023-06-01")
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", 10))

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
    """Remove punctuation marks and formatting for natural speech"""
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
def track_telegram_conversation(user_id, user_message, bot_reply, session_data):
    """Track Telegram conversation in Supabase database"""
    # DISABLED: Using PostgreSQL now - Jan 2026
    return
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
            "https://euyidvolwqmzijkfrplh.supabase.co/functions/v1/submit-progress",
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
    """Update last activity timestamp for connected bot"""
    try:
        payload = {
            "telegram_user_id": str(user_id),
            "last_activity": datetime.now().isoformat()
        }
        
        response = requests.post(
            "https://euyidvolwqmzijkfrplh.supabase.co/functions/v1/update-bot-activity",
            json=payload,
            headers={
                "Authorization": f"Bearer {os.environ.get('SUPABASE_ANON_KEY')}",
                "Content-Type": "application/json"
            },
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✅ Updated activity for user {user_id}")
        else:
            print(f"⚠️ Failed to update activity: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error updating bot activity: {e}")

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
    Check if user has access. Now includes FREE TRIAL for everyone!
    
    Access granted if:
    1. User is within free trial period (14 days, 60 for org members)
    2. User has PayPal subscription (future)
    3. User has valid org code
    4. User is in legacy subscribers.json
    """
    user_id = str(user_id)
    
    # === FREE TRIAL SYSTEM (NEW - Jan 2026) ===
    try:
        # Check free trial status
        trial_file = "user_trials.json"
        trials = {}
        
        if os.path.exists(trial_file):
            with open(trial_file, "r") as f:
                trials = json.load(f)
        
        if user_id in trials:
            # User exists, check trial status
            user_trial = trials[user_id]
            start_date = datetime.fromisoformat(user_trial.get("start_date", datetime.now().isoformat()))
            trial_days = user_trial.get("trial_days", 14)
            org_code = user_trial.get("org_code")
            
            # Check if trial is still valid
            days_elapsed = (datetime.now() - start_date).days
            if days_elapsed <= trial_days:
                print(f"✅ User {user_id} has valid trial ({days_elapsed}/{trial_days} days)")
                return True
            else:
                # Trial expired, but still allow access during transition period
                if days_elapsed <= trial_days + 7:  # 7 day grace period
                    print(f"⚠️ User {user_id} trial expired but in grace period")
                    return True
        else:
            # New user - automatically start free trial!
            trials[user_id] = {
                "start_date": datetime.now().isoformat(),
                "trial_days": 14,  # Default 14 days
                "org_code": None,
                "status": "trial"
            }
            with open(trial_file, "w") as f:
                json.dump(trials, f, indent=2)
            print(f"🎉 New user {user_id} - started 14-day free trial!")
            return True
            
    except Exception as e:
        print(f"⚠️ Trial check error: {e} - allowing access")
        return True  # On error, allow access
    
    # === LEGACY: Check old Gumroad subscribers ===
    try:
        with open("subscribers.json", "r") as f:
            subscribers = json.load(f)
        for email, info in subscribers.items():
            if str(info.get("telegram_id")) == str(user_id) and info.get("status") == "active":
                return True
    except Exception as e:
        print(f"⚠️ Legacy subscription check error: {e}")
    
    # === FUTURE: PayPal subscription check will go here ===
    
    # Default: Allow access (for now - remove blocking)
    print(f"ℹ️ User {user_id} - allowing access (trial system active)")
    return True  # Changed from False to True - no blocking!

# === EMOTIONAL INTELLIGENCE & PERSONALIZATION ===
FAMILY_MEMBERS = {
    "alisa": {
        "role": "child",
        "age": 4,
        "learning_level": "beginner",
        "interests": ["animals", "colors", "games", "songs"],
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
    # Detect family member
    family_member = detect_family_member(user_info, message_text) 
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
                    "mastered_words": []
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
    user_name = session["context"]["user"]["preferences"].get("user_name", "friend")
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

    # Add family member customization
    if family_role == "alisa":
        system_content += """
You're speaking with Alisa, a 4-year-old child learning basic Spanish and English. Use simple language, be playful and warm, use emojis, and focus on basic vocabulary with simple sentences. 
Keep words and concepts appropriate for a preschooler. Use repetition and positive reinforcement.
When teaching Spanish, try to relate it to things a child would be interested in like animals, colors, and simple games.
"""
    elif family_role == "marina":
        system_content += """
You're speaking with Marina, a 65-year-old learning Spanish and English. Be respectful, patient, and provide clear explanations with common examples. 
Use short sentences with straightforward vocabulary. Explain cultural context when relevant. Be supportive and encouraging, recognizing the challenge of learning languages later in life.
Focus on practical, everyday phrases that would be useful in Panama.
"""
    else:  # default adult user
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
            system_content += f"Family: {family_info}\n"
        
        system_content += """
Provide nuanced language assistance focused on natural conversation, idioms, and practical vocabulary. 
Use vocabulary appropriate for their level. ALWAYS address them by their actual name, not "Elena".
"""

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
        if level == "beginner":
            topics = ["Colors and shapes", "Animals", "Numbers 1-10", "Family members"]
        else:
            topics = ["Common verbs", "School items", "Simple questions", "Days of the week"]

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
    """Translate the input text to both Spanish and English"""
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": f"Translate this message into both Spanish and English:\n\n{text}"}]
    }
    try:
        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=30)
        res_json = res.json()
        
        # Check for API errors
        if "error" in res_json:
            error_msg = res_json.get("error", {}).get("message", "Unknown API error")
            print(f"OpenAI API error: {error_msg}")
            return None  # Return None instead of error message
        
        # Check for valid response structure
        if "choices" in res_json and len(res_json["choices"]) > 0:
            return res_json["choices"][0]["message"]["content"]
        else:
            print(f"Unexpected API response: {res_json}")
            return None
            
    except requests.exceptions.Timeout:
        print("Translation timeout")
        return None
    except Exception as e:
        print(f"Translation error: {e}")
        return None  # Return None, let caller handle gracefully
def ask_claude_with_mcp(session, translated_input):
    """Use Claude API with fallback to GPT-4, both formatted for bilingual response and video script."""

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
        res = requests.post("https://api.anthropic.com/v1/messages",
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

        # === FALLBACK TO OPENAI GPT-4 ===
        try:
            print("🔁 Falling back to GPT-4 via OpenAI...")

            content_input = translated_input if translated_input else user_message or "Hello"
            gpt_payload = {
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "system",
                        "content": """You are Espaluz, a bilingual emotionally intelligent Spanish-English language tutor for expat families.

Your answers must have TWO PARTS:

1️⃣ A full bilingual text message with emotional tone and context.

2️⃣ Then add a short second section inside [VIDEO SCRIPT START] and [VIDEO SCRIPT END], like:

[VIDEO SCRIPT START]
Hola! Hoy vamos a aprender algo nuevo.
Hello! Today we will learn something new.
[VIDEO SCRIPT END]

This second block will be spoken in video, so keep it short, warm, and clear.
NO emojis in the video script - they will be pronounced!

📝 FORMATTING RULES:
- NEVER use **asterisks** for bold - they show raw!
- Use EMOJIS GENEROUSLY: ✅ ❌ 💡 🗣️ 📖 🌎 🎯 ☕ 🍽️ 🏖️ 🏫 🏥 🏦 🎓
- Start each section with a relevant emoji
- Emojis will be stripped from video script automatically"""
                    },
                    {"role": "user", "content": content_input}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }

            gpt_headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }

            gpt_res = requests.post("https://api.openai.com/v1/chat/completions",
                                    headers=gpt_headers,
                                    json=gpt_payload)

            print(f"GPT-4 fallback status: {gpt_res.status_code}")
            print(f"GPT-4 fallback raw: {gpt_res.text}")

            gpt_result = gpt_res.json()
            gpt_text = gpt_result["choices"][0]["message"]["content"]
            short_text = extract_video_script(gpt_text)

            return gpt_text.strip(), short_text.strip(), ""

        except Exception as gpt_error:
            print(f"❌ GPT-4 fallback failed: {gpt_error}")
            return (
                "Lo siento, hubo un error. Sorry, there was an error.",
                "Español: Lo siento. English: Sorry about that.",
                ""
            )

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

        # 7. Send the video
        with open(output_video, "rb") as video_file:
            bot.send_video(chat_id, video_file)

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

        # Send the voice message
        with open(voice_file, "rb") as voice:
            bot.send_voice(chat_id, voice)

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
from gtts import gTTS

def bulletproof_video_generator(chat_id, full_reply_text):
    print("🚀 ENTERED bulletproof_video_generator")
    try:
        match = re.search(r"\[VIDEO SCRIPT START\](.*?)\[VIDEO SCRIPT END\]", full_reply_text, re.DOTALL)
        if not match:
            print("❌ No [VIDEO SCRIPT START] block found in Claude response.")
            return False

        short_reply = match.group(1).strip()
        
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
        output_video = "bp_video.mp4"

        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-i", base_video,
            "-i", audio_path,
            "-map", "0:v:0",  # take only video stream from base video
            "-map", "1:a:0",  # take only audio stream from mp3
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            output_video
        ]

        print("🎬 Merging audio with looped video using FFmpeg...")
        subprocess.run(ffmpeg_command, check=True)

        # === STEP 4: Send video to Telegram
        with open(output_video, "rb") as video_file:
            bot.send_video(chat_id, video_file)
            print("📤 Video sent successfully!")

        # === STEP 5: Cleanup
        os.remove(audio_path)
        os.remove(output_video)
        return True

    except Exception as e:
        print(f"❌ Error in bulletproof_video_generator: {e}")
        return False

def send_full_voice_message(chat_id, full_reply_text):
    try:
        # ENHANCEMENT: Clean the full text too
        full_reply_clean = clean_text_for_speech(full_reply_text)
        print(f"🎧 Generating voice with cleaned text, length: {len(full_reply_clean)}")
        
        tts = gTTS(text=full_reply_clean, lang="es")
        tts.save("simple_voice.mp3")
        with open("simple_voice.mp3", "rb") as f:
            bot.send_voice(chat_id, f)
        os.remove("simple_voice.mp3")
        print("✅ Voice message sent successfully")
    except Exception as e:
        print(f"❌ Voice message error: {e}")

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

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4o",
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

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            extracted_text = result["choices"][0]["message"]["content"]
            
            # ENHANCEMENT: Add text length info
            word_count = len(extracted_text.split())
            return f"📄 Extracted {word_count} words:\n\n{extracted_text}"
        else:
            return "❌ GPT-4o did not return a usable response."

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
        send_full_voice_message(chat_id, full_reply)
        
        print(f"✅ Multimedia generation complete - Video: {'Success' if video_success else 'Failed'}, Voice: Sent")
            
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

    # Init session
    if user_id not in user_sessions:
        user_sessions[user_id] = create_initial_session(user_id, message_obj.from_user, message_obj.chat, user_input)
        print(f"Created new session for user {user_id}")

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

    # Send the main response
    bot.send_message(chat_id, f"🤖 Espaluz:\n{strip_markdown_formatting(full_reply)}")
    print("Main text response sent")

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

    # Init session
    if user_id not in user_sessions:
        user_sessions[user_id] = create_initial_session(user_id, message_obj.from_user, message_obj.chat, user_input)
        print(f"Created new session for user {user_id}")

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

    # Send the main response
    bot.send_message(chat_id, f"🤖 Espaluz:\n{strip_markdown_formatting(full_reply)}")
    print("Main text response sent")

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
        track_telegram_conversation(user_id, user_input, full_reply, session)
        update_connected_bot_activity(user_id)
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

# === HANDLERS ===
@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = str(message.from_user.id)
    
    # Track activity if enhanced brain available
    if ENHANCED_BRAIN_AVAILABLE:
        try:
            track_activity(user_id)
        except:
            pass
    
    # Always reset to start of onboarding for /start
    set_user_onboarding(user_id, {"step": "country"})
    
    # Start onboarding - ask for country first
    welcome_msg = ONBOARDING_MESSAGES["country"]
    
    bot.send_message(message.chat.id, welcome_msg)

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

        response = requests.post(
            "https://euyidvolwqmzijkfrplh.supabase.co/functions/v1/connect-bot",
            json=payload,
            headers={
                "Authorization": f"Bearer {os.environ.get('SUPABASE_ANON_KEY')}",
                "Content-Type": "application/json"
            },
            timeout=5
        )

        if response.status_code == 200:
            bot.reply_to(message, "✅ Bot successfully connected to your account!")
        else:
            print("❌ Connect-bot error:", response.status_code, response.text)
            bot.reply_to(message, f"⚠️ Connection failed:\n{response.status_code} {response.text}")

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
/link — Link Subscription ID
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
    """Show local slang for a country"""
    if not ENHANCED_BRAIN_AVAILABLE:
        bot.reply_to(message, "Slang module not available.")
        return
    
    parts = message.text.split()
    if len(parts) > 1:
        country = parts[1].lower()
        slang_text = get_slang(country)
        bot.reply_to(message, slang_text, parse_mode="Markdown")
    else:
        # Default to Panama, show available options
        response = SLANG_PANAMA + "\n\n💡 *Other countries:*\n"
        response += "/slang mexico\n/slang colombia\n/slang argentina\n/slang costa_rica"
        bot.reply_to(message, response, parse_mode="Markdown")

@bot.message_handler(commands=["org"])
def handle_org(message):
    """Handle organization code for pilot programs"""
    if not ENHANCED_BRAIN_AVAILABLE:
        bot.reply_to(message, "Organization codes not available.")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, """🏢 *Enter your organization code*

Usage: /org YOUR_CODE

Examples:
• /org AMCHAM_PANAMA
• /org ISP_PARENTS
• /org ISD_MEMBERS

Contact your organization if you don't have a code.""", parse_mode="Markdown")
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
    
    country_name = parts[1].lower().strip()
    
    # Map common names
    country_map = {
        "panama": Country.PANAMA,
        "panamá": Country.PANAMA,
        "mexico": Country.MEXICO,
        "méxico": Country.MEXICO,
        "colombia": Country.COLOMBIA,
        "argentina": Country.ARGENTINA,
        "spain": Country.SPAIN,
        "españa": Country.SPAIN,
        "costa_rica": Country.COSTA_RICA,
        "costarica": Country.COSTA_RICA,
        "peru": Country.PERU,
        "perú": Country.PERU,
        "chile": Country.CHILE,
        "ecuador": Country.ECUADOR
    }
    
    if country_name in country_map:
        country = country_map[country_name]
        context = get_country_context(country)
        
        user_id = str(message.from_user.id)
        if user_id in user_sessions:
            user_sessions[user_id]["context"]["user"]["preferences"]["country"] = country_name
        
        response = f"""✅ *Country set: {context.get('flag', '')} {context.get('name', country_name.title())}*

💰 Currency: {context.get('currency', 'Local currency')}
🕐 Timezone: {context.get('timezone', 'Local time')}

I'll now use local vocabulary and expressions!

Try: /slang {country_name} to see local expressions."""
        bot.reply_to(message, response, parse_mode="Markdown")
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

def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file using OpenAI Whisper (SDK v1.0+)"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        with open(audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )
        return transcript

    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return None

@bot.message_handler(commands=["link"])
def handle_link(message):
    link_msg = f"""📩 Link Your Subscription

You're currently on a FREE TRIAL - enjoy all features!

After trial ends:
• Monthly: $11/month (includes 14-day FREE trial!)

💳 PayPal (ready now):
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

@bot.message_handler(commands=["convo"])
def handle_convo(message):
    """Toggle conversation mode for real-time voice translation"""
    user_id = str(message.from_user.id)
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if args and args[0].lower() == "off":
        result = conversation_mode.deactivate(user_id)
        bot.send_message(message.chat.id, result)
        return
    
    # Determine target language
    target_lang = "es"  # Default
    if args:
        arg = args[0].lower()
        if arg in ["es", "spanish", "español"]:
            target_lang = "es"
        elif arg in ["en", "english", "inglés", "ingles"]:
            target_lang = "en"
    
    result = conversation_mode.activate(user_id, target_lang)
    bot.send_message(message.chat.id, result, parse_mode="Markdown")


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
        temp_output = f"convo_out_{message.message_id}.ogg"
        
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
        target_lang = conversation_mode.get_target_language(user_id)
        translate_to = get_opposite_language(detected_lang, target_lang)
        
        # 4. Quick translate with Claude
        client = anthropic.Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))
        prompt = get_quick_translate_prompt(transcription, detected_lang, translate_to)
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        translation = response.content[0].text.strip()
        
        # 5. Generate voice response
        tts_lang = "es" if translate_to == "es" else "en"
        # Use Neural TTS for beautiful voice
        if NEURAL_TTS_AVAILABLE:
            try:
                neural_path = generate_voice_sync(translation, lang=tts_lang, style="conversation", message_id=message.message_id)
                if neural_path:
                    import shutil
                    shutil.copy(neural_path, temp_mp3)
                    if neural_path != temp_mp3:
                        os.remove(neural_path)
                else:
                    raise Exception("Neural TTS returned None")
            except Exception as e:
                print(f"Neural TTS failed: {e}, using gTTS")
                tts = gTTS(text=translation, lang=tts_lang, slow=False)
                tts.save(temp_mp3)
        else:
            tts = gTTS(text=translation, lang=tts_lang, slow=False)
            tts.save(temp_mp3)
        
        # Convert to OGG for Telegram voice note
        subprocess.run([
            "ffmpeg", "-y", "-i", temp_mp3,
            "-c:a", "libopus", "-b:a", "64k",
            temp_output
        ], capture_output=True, check=True)
        
        # 6. Send voice note + text
        lang_flag = "🇪🇸" if translate_to == "es" else "🇬🇧"
        bot.send_message(chat_id, f"🎤 *{transcription}*\n{lang_flag} {translation}", parse_mode="Markdown")
        
        with open(temp_output, "rb") as voice:
            bot.send_voice(chat_id, voice)
        
        # Track usage
        conversation_mode.increment_count(user_id)
        
        # Cleanup
        for f in [temp_ogg, temp_mp3, temp_output]:
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
• $11/month - Full access, family included
• 14-day FREE trial included!

💳 Subscribe via PayPal:
{PAYPAL_SUBSCRIPTION_LINK}

🔑 After subscribing:
Send me your Subscription ID (I-XXXXXXXXXXXX) to activate instantly!
Find it in your PayPal confirmation or Settings → Payments → Automatic payments

✨ Your Spanish learning journey awaits!"""
    
    bot.send_message(message.chat.id, sub_msg)


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
    """Fast translation for conversation mode - minimal latency"""
    try:
        # Use Claude for accurate translation
        prompt = f"""Translate the following text from {source_lang} to {target_lang}.
ONLY output the translation, nothing else. No explanations, no quotes, just the translated text.

Text: {text}

Translation:"""
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            translation = result["content"][0]["text"].strip()
            return translation
        else:
            print(f"Translation API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Quick translate error: {e}")
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

@bot.message_handler(commands=["convo"])
def handle_convo_toggle(message):
    """Toggle conversation mode on/off"""
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
                bot.send_voice(chat_id, audio)
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
    # If conversation mode is active, use fast translation instead of full tutor mode
    if conversation_mode.is_active(user_id):
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
    
    # Free trial is now active for everyone!
    # Legacy subscription check kept for future PayPal integration
    if not is_subscribed(user_id):
        # This should rarely trigger now with free trial
        bot.reply_to(message, "🎉 Welcome! Your 14-day free trial has started.\n\nSend me a voice message to practice!")
        return

    try:
        file_info = bot.get_file(message.voice.file_id)
        voice_file = bot.download_file(file_info.file_path)

        temp_ogg_path = f"input_{message.message_id}.ogg"
        temp_mp3_path = f"input_{message.message_id}.mp3"

        with open(temp_ogg_path, "wb") as f:
            f.write(voice_file)

        subprocess.run(["ffmpeg", "-i", temp_ogg_path, temp_mp3_path], check=True)

        transcription = transcribe_audio(temp_mp3_path)

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
        bot.send_message(message.chat.id, f"🗣️ Transcripción:\n{transcription}")

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

    # Free trial is now active for everyone!
    if not is_subscribed(user_id):
        bot.reply_to(message, "🎉 Welcome! Your 14-day free trial has started.\n\nJust send me any message to start learning!")
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
    BotCommand("start", "Start Espaluz"),
    BotCommand("reset", "Reset learning session"),
    BotCommand("progress", "Show learning progress"),
    BotCommand("family", "Switch family member"),
    BotCommand("help", "Help and instructions")
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

# Fix photo handler - make it more resilient to errors
@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    """Handle photo message with text recognition and translation"""
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
