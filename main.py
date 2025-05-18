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
import threading

# Load env
load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL_NAME", "claude-3-7-sonnet-20250219")
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
            delete_result = requests.get(delete_url, timeout=30).json()
            print(f"🧹 Webhook deletion result: {delete_result}")
            info = requests.get(info_url, timeout=30).json()
            if not info.get('result', {}).get('url'):
                print(f"✅ No webhook found in cycle #{killer_cycle}")
            else:
                print(f"⚠️ WARNING: Webhook still exists: {info['result']['url']}")
            time.sleep(webhook_check_interval)
        except Exception as e:
            print(f"❌ Webhook killer error: {e}")
            time.sleep(60)

print("Checking FFmpeg installation...")
try:
    ffmpeg_version = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True).stdout.split('\n')[0]
    print(f"✅ FFmpeg is available: {ffmpeg_version}")
    ffprobe_version = subprocess.run(["ffprobe", "-version"], capture_output=True, text=True, check=True).stdout.split('\n')[0]
    print(f"✅ FFprobe is available: {ffprobe_version}")
    FFMPEG_AVAILABLE = True
except Exception as e:
    print(f"❌ FFmpeg check failed: {e}")
    FFMPEG_AVAILABLE = False

def create_test_video():
    base_video = "espaluz_loop.mp4"
    if not os.path.exists(base_video) and FFMPEG_AVAILABLE:
        print("Creating base video...")
        try:
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=640x480:d=5", "-c:v", "libx264", base_video], check=True, capture_output=True)
            if os.path.exists(base_video):
                print(f"✅ Created test video: {base_video}")
        except Exception as e:
            print(f"❌ Error creating test video: {e}")

create_test_video()

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_sessions = {}

threading.Thread(target=webhook_killer_thread, daemon=True).start()

# === MULTIMEDIA GENERATOR ===
def railway_optimized_multimedia(chat_id, full_reply_text):
    print("🔄 Starting Railway-optimized multimedia generator")
    match = re.search(r"\[VIDEO SCRIPT START\](.*?)\[VIDEO SCRIPT END\]", full_reply_text, re.DOTALL)
    video_script = match.group(1).strip() if match else "¡Hola! Estoy aquí para ayudarte con español. Hello! I'm here to help you with Spanish."
    voice_text = re.sub(r"\[VIDEO SCRIPT START\].*?\[VIDEO SCRIPT END\]", "", full_reply_text, re.DOTALL).strip()
    if len(voice_text) > 1500:
        voice_text = voice_text[:1500] + "..."
    timestamp = int(time.time())
    voice_file = f"voice_{timestamp}.mp3"
    try:
        tts = gTTS(text=voice_text, lang="es", slow=False)
        tts.save(voice_file)
        if os.path.exists(voice_file) and os.path.getsize(voice_file) > 1000:
            with open(voice_file, "rb") as f:
                bot.send_voice(chat_id, f)
                print("✅ Voice message sent successfully")
    except Exception as e:
        print(f"❌ Voice error: {e}")
    finally:
        if os.path.exists(voice_file): os.remove(voice_file)

    try:
        video_audio = f"video_audio_{timestamp}.mp3"
        output_video = f"output_video_{timestamp}.mp4"
        tts = gTTS(text=video_script, lang="es", slow=False)
        tts.save(video_audio)
        base_video = "espaluz_loop.mp4"
        if not os.path.exists(base_video):
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=640x480:d=5", "-c:v", "libx264", base_video], check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-y", "-i", base_video, "-i", video_audio, "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-shortest", output_video], check=True, capture_output=True)
        if os.path.exists(output_video) and os.path.getsize(output_video) > 10000:
            with open(output_video, "rb") as f:
                bot.send_video(chat_id, f)
                print("✅ Video sent successfully")
    except Exception as e:
        print(f"❌ Video error: {e}")
    finally:
        for file in [video_audio, output_video]:
            if os.path.exists(file): os.remove(file)

# === MAIN LOGIC ===
def process_message(user_input, chat_id, user_id, message_obj):
    print(f"⭐️ Processing message from user {user_id}: {user_input[:30]}...")
    if user_id not in user_sessions:
        user_sessions[user_id] = create_initial_session(user_id, message_obj.from_user, message_obj.chat, user_input)
    session = user_sessions[user_id]
    session["context"]["conversation"]["message_count"] += 1
    session["context"]["conversation"]["last_interaction_time"] = datetime.now().isoformat()
    translated = translate_to_es_en(user_input)
    bot.send_message(chat_id, f"📝 Traducción:\n{translated}")
    session["messages"].append({"role": "user", "content": user_input})
    full_reply, short_reply, thinking_process = ask_claude_with_mcp(session, translated)
    bot.send_message(chat_id, f"🤖 Espaluz:\n{full_reply}")
    if thinking_process:
        summary = f"🧠 *Thinking Process*:\n\n{thinking_process[:500]}..."
        if len(thinking_process) > 500: summary += "\n\n(Thinking process summarized for brevity)"
        bot.send_message(chat_id, summary, parse_mode="Markdown")
    session["messages"].append({"role": "assistant", "content": full_reply})

    print("Starting multimedia generation thread...")
    media_thread = threading.Thread(
        target=railway_optimized_multimedia,
        args=(chat_id, full_reply),
        daemon=True
    )
    media_thread.start()

    print("Updating learning data...")
    family_member = session["context"]["user"]["preferences"]["family_role"]
    learned_items = enhance_language_learning_detection(full_reply, family_member, session)
    session = update_session_learning(session, learned_items)
    session = adapt_learning_path(session, user_input, full_reply)
    print("Learning data updated")