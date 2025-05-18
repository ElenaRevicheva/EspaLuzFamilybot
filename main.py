import os
import time
import uuid
import json
import requests
import subprocess
from datetime import datetime, timedelta
from gtts import gTTS
from dotenv import load_dotenv
import telebot
import re
from PIL import Image
import pytesseract
import io
import base64
import math


# Load env
load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL_NAME", "claude-3-7-sonnet-20250219")
CLAUDE_API_VERSION = os.environ.get("CLAUDE_API_VERSION", "2023-06-01")  # Updated to allow for version changes
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", 10))

# === WEBHOOK KILLER THREAD ===
def webhook_killer_thread():
    """Background thread that continuously monitors and removes webhooks"""
    print("🔥🔥🔥 WEBHOOK KILLER THREAD STARTING 🔥🔥🔥")
    
    webhook_check_interval = 30  # seconds between checks
    killer_cycle = 0
    
    while True:
        try:
            killer_cycle += 1
            print(f"🛡️ Webhook killer check cycle #{killer_cycle}")
            
            # Execute webhook deletion
            delete_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook?drop_pending_updates=true"
            info_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
            
            # Delete webhook
            delete_response = requests.get(delete_url, timeout=30)
            delete_result = delete_response.json()
            print(f"🧹 Webhook deletion result: {delete_result}")
            
            # Verify webhook status
            info_response = requests.get(info_url, timeout=30)
            webhook_info = info_response.json()
            webhook_url = webhook_info.get('result', {}).get('url', '')
            
            if webhook_url:
                print(f"⚠️ WARNING: Webhook still exists: {webhook_url}! Trying again...")
            else:
                print(f"✅ No webhook found in cycle #{killer_cycle}")
            
            # Sleep before next check
            time.sleep(webhook_check_interval)
        except Exception as e:
            print(f"❌ Webhook killer error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(60)  # Wait longer after errors

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

# Create a simple test video file if needed (can add before Flask app runs)
def create_test_video():
    """Create a simple test video file if the base video doesn't exist"""
    base_video = "espaluz_loop.mp4"
    if not os.path.exists(base_video) and FFMPEG_AVAILABLE:
        print("Base video not found, creating a simple test video...")
        try:
            # Create a 5-second color video
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

# Call this before starting the Flask app
create_test_video()

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_sessions = {}

# Start webhook killer thread
import threading
webhook_thread = threading.Thread(target=webhook_killer_thread, daemon=True)
webhook_thread.start()
print("🛡️ Webhook killer thread started in background")

def debug_file_paths():
    """Debug function to check important file paths"""
    base_video = "espaluz_loop.mp4"
    base_video_abs = os.path.abspath(base_video)

    print(f"Current working directory: {os.getcwd()}")
    print(f"Base video relative path: {base_video}")
    print(f"Base video absolute path: {base_video_abs}")
    print(f"Base video exists: {os.path.exists(base_video_abs)}")

    # List files in current directory
    files = os.listdir(".")
    print(f"Files in current directory: {files}")

    # Check FFmpeg
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
        ffmpeg_version = result.stdout.split('\n')[0]
        print(f"FFmpeg version: {ffmpeg_version}")
    except Exception as e:
        print(f"FFmpeg check error: {e}")

# Call this function before the Flask app starts
debug_file_paths()

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
    """Advanced emotion detection with learning capabilities"""
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

    # Find dominant emotion
    dominant = max(combined_emotions.items(), key=lambda x: x[1]) if combined_emotions else ("neutral", 1.0)

    # Add confidence metric
    confidence = dominant[1] / sum(combined_emotions.values()) if sum(combined_emotions.values()) > 0 else 0.5

    # Add emotional progression analysis
    progression_analysis = analyze_emotional_progression(dominant[0], session)

    return {
        "dominant_emotion": dominant[0],
        "confidence": confidence,
        "emotion_data": combined_emotions,
        "progression": progression_analysis
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

def add_panama_cultural_context(prompt, session):
    """Add Panama-specific cultural context to learning prompts"""
    # Get family member
    family_role = session["context"]["user"]["preferences"]["family_role"]

    # Add Panama-specific cultural context
    panama_context = """
Use these Panama-specific cultural references in your teaching:

Geography: Panama connects North and South America, with the Panama Canal as its most famous feature.
Language: Panamanians speak Spanish with unique local expressions like "¿Qué xopá?" (What's up?)
Food: Common dishes include sancocho (chicken soup), patacones (fried plantains), and ceviche.
Daily Life: In Panama City, people navigate between modern skyscrapers and the colonial Casco Viejo district.
Cultural Mix: Panama has influences from Indigenous peoples, Africans, Spanish colonizers, and Americans.
Weather: Panama has a tropical climate with a rainy season (May-November) and dry season (December-April).
"""

    # Adjust cultural context based on family member
    if family_role == "alisa":
        panama_context += """
For a child: Focus on simple concepts like Panamanian animals (harpy eagle, jaguar), 
fruits (mango, pineapple), and basic greetings used by Panamanian children.
"""
    elif family_role == "marina":
        panama_context += """
For an elder: Focus on traditional aspects of Panama like the pollera (national dress),
traditional folklore dances like the tamborito, and markets/shopping terminology.
"""
    else:  # elena
        panama_context += """
For a working parent: Focus on professional vocabulary, education system terminology,
and everyday phrases needed for work, shopping, and managing a household in Panama.
"""

    # Combine with original prompt
    enhanced_prompt = prompt + "\n\n" + panama_context

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
    system_content = "You are Espaluz, a bilingual emotionally intelligent AI language tutor for a Russian expat family in Panama."

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
    else:  # elena / default
        system_content += """
You're speaking with Elena, a 39-year-old parent who is at an intermediate level in Spanish and English. 
She's looking to improve her conversational fluency while managing daily language tasks and helping her daughter learn too.
Provide nuanced language assistance focused on natural conversation, idioms, and practical vocabulary. 
You can use more complex grammar structures and vocabulary with her.
"""

    # Add enhanced emotional intelligence from context
    system_content += f"""

I notice that the user's emotional state appears to be: {emotion.upper()} (confidence: {emotion_confidence:.2f}).
Emotional progression: {emotion_progression}. 
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

    # Add Panama-specific cultural context
    system_content = add_panama_cultural_context(system_content, session)

    # Add response format instructions
    system_content += """
    Your answer should have TWO PARTS:

    1️⃣ A full, thoughtful bilingual response (using both Spanish and English):
       - Respond naturally to the message
       - Be emotionally aware, friendly, and motivating
       - Include relevant Spanish learning or cultural context (from Panama or daily life)
       - Use vocabulary appropriate for the user's level

    2️⃣ A second short block inside [VIDEO SCRIPT START] ... [VIDEO SCRIPT END] for video:
       - Must be 2 to 4 concise sentences MAX
       - Use both Spanish and English
       - Tone: warm, clear, and simple for spoken delivery
       - It will be spoken by an avatar on video, so make it suitable for audio (not robotic or boring!)
       - Example:

    [VIDEO SCRIPT START]
    ¡Hola Elena! Hoy es un gran día para aprender. 
    Hello Elena! Today is a great day to learn.
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
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": f"Translate this message into both Spanish and English:\n\n{text}"}]
    }
    try:
        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Translation error: {e}")
        return f"Error in translation: {e}"

def ask_claude_with_mcp(session, translated_input):
    """Use Claude 3.7 with advanced context embedding and improved script handling"""
    # Prepare MCP request
    user_message = session["messages"][-1]["content"] if session["messages"] else ""

    # Check for complex language learning topics that would benefit from extended thinking
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

        result = res.json()

        # Check for thinking output if extended thinking was enabled
        thinking_process = ""
        if "thinking" in result:
            thinking_process = result["thinking"]
            # Store thinking process in session for learning analytics
            if "extended_thinking_history" not in session:
                session["extended_thinking_history"] = []
            session["extended_thinking_history"].append({
                "query": user_message,
                "thinking": thinking_process,
                "timestamp": datetime.now().isoformat()
            })

        full_reply = result["content"][0]["text"]

        # Use improved video script extraction
        short_text = extract_video_script(full_reply)

        return full_reply.strip(), short_text.strip(), thinking_process

    except Exception as e:
        print(f"Claude API error: {e}")
        if 'res' in locals():
            print(f"Response: {res.text}")
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
        # === STEP 1: Extract short reply from [VIDEO SCRIPT START]...END
        match = re.search(r"\[VIDEO SCRIPT START\](.*?)\[VIDEO SCRIPT END\]", full_reply_text, re.DOTALL)
        if not match:
            print("❌ No [VIDEO SCRIPT START] block found in Claude response.")
            return False

        short_reply = match.group(1).strip()
        print(f"📝 Extracted short reply for video: '{short_reply}'")

        # === STEP 2: Generate TTS audio
        tts = gTTS(text=short_reply, lang="es")  # You can change to 'es' or 'en' if needed
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
        print(f"🎧 Generating full voice message with text length: {len(full_reply_text)}")
        tts = gTTS(text=full_reply_text, lang="es")
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
    """Process photo using GPT-4o Vision only (no Tesseract fallback)"""
    try:
        # Open the image from bytes
        image = Image.open(io.BytesIO(photo_file))

        # Resize if necessary to keep it manageable
        max_size = 1024
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.LANCZOS)

        # Convert to base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Build GPT-4o request
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts and translates text from images. Identify the language, and provide translations to both Spanish and English."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract any text from this image, detect its original language, and translate it to both Spanish and English."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000
        }

        # Send request
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        result = response.json()

        # Handle result
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "❌ GPT-4o did not return a usable response."

    except Exception as e:
        print(f"Error in GPT-4o image processing: {e}")
        return "❌ Error processing the image with GPT-4o. Please try again later."

# === MAIN LOGIC ===
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

    # Get translation
    translated = translate_to_es_en(user_input)
    bot.send_message(chat_id, f"📝 Traducción:\n{translated}")
    print("Translation sent")

    # Update message history
    session["messages"].append({"role": "user", "content": user_input})

    # Get Claude response with MCP
    print("Requesting Claude response...")
    full_reply, short_reply, thinking_process = ask_claude_with_mcp(session, translated)
    print(f"Received Claude response, length: {len(full_reply)}")

    # Send the main response
    bot.send_message(chat_id, f"🤖 Espaluz:\n{full_reply}")
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

    # Launch multimedia generation in a thread with clear separation
    print("Starting multimedia generation thread...")

    def ultimate_multimedia_generator(chat_id, full_reply_text, short_reply_text):
        print("Starting ultimate multimedia generation...")

        # === STEP 1: Create video from short [VIDEO SCRIPT] reply ===
        success = bulletproof_video_generator(chat_id, full_reply_text)  # 🔥 Fixed here
        if success:
            print("Video generation result: SUCCESS")
        else:
            print("Video generation result: ❌ FAILURE")

        # === STEP 2: Create full voice message from full text ===
        try:
            print(f"Starting voice message generation with text length: {len(full_reply_text)}")
            # Remove [VIDEO SCRIPT START] block from voice message
            simplified_text = re.sub(r"\[VIDEO SCRIPT START\](.*?)\[VIDEO SCRIPT END\]", "", full_reply_text, flags=re.DOTALL).strip()
            print(f"Generating simplified voice message with text length: {len(simplified_text)}")

            tts = gTTS(text=simplified_text, lang="es")
            voice_path = "simple_voice.mp3"
            tts.save(voice_path)
            print(f"Voice file created: {voice_path}, size: {os.path.getsize(voice_path)} bytes")

            with open(voice_path, "rb") as voice_file:
                bot.send_voice(chat_id, voice_file)
                print("Voice message sent with ID: ✅")

            os.remove(voice_path)
            print("Voice message result: SUCCESS\nBoth video and voice completed successfully!")

        except Exception as e:
            print(f"❌ Error generating voice message: {e}")

    media_thread = threading.Thread(
    target=railway_optimized_multimedia,
    args=(chat_id, full_reply),
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

# === HANDLERS ===
@bot.message_handler(commands=["start"])
def handle_start(message):
    """Handle /start command"""
    user_id = str(message.from_user.id)
    user_sessions[user_id] = create_initial_session(user_id, message.from_user, message.chat)

    # Create personalized welcome based on detected family member
    family_member = user_sessions[user_id]["context"]["user"]["preferences"]["family_role"]
    member_info = FAMILY_MEMBERS.get(family_member, FAMILY_MEMBERS["elena"])

    welcome_msg = (
        "👋 ¡Hola! Soy Espaluz, tu asistente de idiomas. / Hello! I'm Espaluz, your language assistant.\n\n"
        "☕ *If you enjoy Espaluz and want to support this project,*\n"
        "👉 [Buy me a coffee](https://buymeacoffee.com/aideazz)\n\n"
        "Your support helps families learn Spanish with emotional, intelligent AI 💛\n\n"
    )

    if family_member == "alisa":
        welcome_msg += "🎮 ¡Vamos a aprender español y inglés jugando! / Let's learn Spanish and English while playing!"
    elif family_member == "marina":
        welcome_msg += "📚 Estoy aquí para ayudarte a aprender español e inglés a tu ritmo. / I'm here to help you learn Spanish and English at your own pace."
    else:
        welcome_msg += "🗣️ Estoy aquí para ayudarte con tus necesidades de idiomas. / I'm here to help with your language needs."

    welcome_msg += "\n\nEnvíame un mensaje de voz o texto para comenzar. / Send me a voice or text message to begin."
    welcome_msg += "\n\n📸 ¡También puedes enviarme fotos de texto para traducirlo! / You can also send me photos of text to translate it!"

    bot.reply_to(message, welcome_msg, parse_mode="Markdown")

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

@bot.message_handler(commands=["family"])
def handle_family(message):
    """Handle /family command to set family member identification"""
    user_id = str(message.from_user.id)
    if user_id not in user_sessions:
        user_sessions[user_id] = create_initial_session(user_id, message.from_user, message.chat)

    # Extract family member name if provided
    command_parts = message.text.split()
    if len(command_parts) > 1:
        member_name = command_parts[1].lower()
        if member_name in FAMILY_MEMBERS:
            user_sessions[user_id]["context"]["user"]["preferences"]["family_role"] = member_name
            member_info = FAMILY_MEMBERS[member_name]
            bot.reply_to(message, f"👪 Perfil cambiado a: {member_name.capitalize()} ({member_info['role']}, {member_info['age']} años) / Profile changed to: {member_name.capitalize()} ({member_info['role']}, {member_info['age']} years old)")
            return

    # If no valid name provided, show options
    family_msg = """👪 *¿Quién eres? / Who are you?*

Usa uno de estos comandos / Use one of these commands:
- /family alisa - Para la niña / For the child (4)
- /family marina - Para la abuela / For the grandmother (65)
- /family elena - Para la madre / For the mother (39)"""

    bot.reply_to(message, family_msg, parse_mode="Markdown")

@bot.message_handler(commands=["help"])
def handle_help(message):
    """Handle /help command"""
    help_text = """🌟 *Comandos de Espaluz / Espaluz Commands:*

/start - Iniciar el bot / Start the bot
/reset - Reiniciar la conversación / Reset the conversation
/progress - Ver tu progreso / View your progress
/family - Cambiar miembro familiar / Change family member
/help - Ver este mensaje / See this message

💬 Puedes enviar mensajes de texto o voz en ruso, español o inglés.
💬 You can send text or voice messages in Russian, Spanish, or English.

📸 ¡Envíame fotos de texto para traducirlo automáticamente! (menús, señales, documentos)
📸 Send me photos of text for automatic translation! (menus, signs, documents)"""

    bot.reply_to(message, help_text, parse_mode="Markdown")

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

@bot.message_handler(content_types=["voice"])
def handle_voice(message):
    try:
        file_info = bot.get_file(message.voice.file_id)
        voice_file = bot.download_file(file_info.file_path)

        temp_ogg_path = f"input_{message.message_id}.ogg"
        temp_mp3_path = f"input_{message.message_id}.mp3"

        # Save OGG
        with open(temp_ogg_path, "wb") as f:
            f.write(voice_file)

        # Convert OGG to MP3 using ffmpeg
        subprocess.run([
            "ffmpeg", "-i", temp_ogg_path, temp_mp3_path
        ], check=True)

        # Transcribe with Whisper or your preferred model
        transcription = transcribe_audio(temp_mp3_path)  # This should use OpenAI Whisper or your existing logic

        if not transcription:
            bot.reply_to(message, "❌ No pude transcribir este mensaje de voz. / I couldn't transcribe this voice message.")
            return

        print(f"📝 Voice transcription: {transcription}")
        bot.send_message(message.chat.id, f"🗣️ Transcripción:\n{transcription}")

        # Continue as a normal text message
        process_message(transcription, message.chat.id, str(message.from_user.id), message)

        # Cleanup
        os.remove(temp_ogg_path)
        os.remove(temp_mp3_path)

    except Exception as e:
        print(f"❌ Error processing voice message: {e}")
        bot.reply_to(message, "❌ Hubo un error al procesar tu mensaje de voz.")

@bot.message_handler(content_types=["text"])
def handle_text(message):
    """Handle text message"""
    process_message(message.text, message.chat.id, str(message.from_user.id), message)

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    """Handle photo message with text recognition and translation"""
    processing_msg = bot.reply_to(message, "🔍 Procesando imagen... / Processing image...")

    try:
        # Step 1: Download the photo
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        photo_file = bot.download_file(file_info.file_path)

        # Step 2: Notify user we're analyzing
        bot.edit_message_text("🔍 Analizando texto... / Analyzing text...",
                              chat_id=message.chat.id,
                              message_id=processing_msg.message_id)

        # Step 3: Extract text from photo
        result = process_photo(photo_file)

        if not result or "Error processing image" in result or "No text found" in result:
            bot.edit_message_text(f"❌ {result or 'No se detectó texto en la imagen. / No text detected in the image.'}",
                                  chat_id=message.chat.id,
                                  message_id=processing_msg.message_id)
            return

        # Step 4: Show extracted translation result
        bot.edit_message_text("📷 Resultado / Result:\n\n" + result,
                              chat_id=message.chat.id,
                              message_id=processing_msg.message_id)

        # Step 5: Enhance learning
        user_id = str(message.from_user.id)
        if user_id in user_sessions:
            family_member = user_sessions[user_id]["context"]["user"]["preferences"]["family_role"]
            learned_items = identify_language_learning_content(result, family_member)
            user_sessions[user_id] = update_session_learning(user_sessions[user_id], learned_items)

        # Step 6: Ask Claude for an explanation
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

        # 🚫 Skip voice and video for photo messages

    except Exception as e:
        bot.edit_message_text(f"❌ Error procesando la imagen: {str(e)}",
                              chat_id=message.chat.id,
                              message_id=processing_msg.message_id)

def debug_files_and_env():
    """Print debugging info about environment and files"""
    print("\n=== DEBUGGING INFO ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Available MP4 files: {[f for f in os.listdir('.') if f.endswith('.mp4')]}")
    print(f"FFmpeg available: {FFMPEG_AVAILABLE}")
    print(f"Python version: {subprocess.check_output(['python', '--version']).decode().strip()}")
    print(f"Disk free space: {subprocess.check_output(['df', '-h', '.']).decode().strip()}")
    print("====================\n")

print("✅ Espaluz is running THIS UPDATED VERSION: v1.5-emotions")

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

print("✅ Espaluz is running THIS UPDATED VERSION: v1.5-emotions (Polling Mode)")

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