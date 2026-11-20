"""EspaLuz PRO ENGLISH on Telegram (20 Nov 2026) - twin of EspaLuzWhatsApp/pro_english_wa.py.

A SEPARATE layer for native Spanish speakers learning professional English. ONE brain for web, WhatsApp and Telegram:
ascent-saas-builder supabase/functions/_shared/pro_english.ts via espaluz-chat `proEnglish`. This file only carries
Telegram text and voice to it and speaks the English back. A linked family keeps one memory in Supabase (the brain finds it
by this Telegram id in connected_bots); a guest's state lives here on the bot's disk. Nothing else in the bot changes.
Plan: cto-aipa docs/espaluz/PRO_ENGLISH_COACH_PLAN_2026-11-20.md
"""
import base64
import json
import os
import re
import subprocess
import threading
import time

import requests

SAAS_FUNCTIONS_URL = "https://euyidvolwqmzijkfrplh.supabase.co/functions/v1"
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pro_english.json")
IDLE_OFF = 3 * 3600
PRO_ON = re.compile(r"^\s*/?(pro english|english pro|ingl[eé]s pro|ingl[eé]s profesional|professional english|"
                    r"pro ingl[eé]s|coach de ingl[eé]s|english coach|proenglish)\b.*$", re.I)
_lock = threading.Lock()

# Set by main.py at startup: the bot's own proven pieces.
BOT = None         # telebot.TeleBot
TRANSCRIBE = None  # transcribe_audio(mp3_path, hint, names) -> str (Groq Whisper -> OpenAI)


def _load():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(state):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)
    os.replace(tmp, STATE_FILE)


def is_active(user_id):
    s = _load().get(str(user_id)) or {}
    return bool(s.get("on")) and time.time() - float(s.get("last") or 0) < IDLE_OFF


def _send(chat_id, text):
    try:
        BOT.send_message(chat_id, text, parse_mode="Markdown")
    except Exception:  # a stray * or _ in a learner's words breaks Markdown: send it plain
        BOT.send_message(chat_id, text.replace("*", "").replace("_", ""))


def _brain(user_id, chat_id, said=None, start=False, audio=None):
    uid = str(user_id)
    with _lock:
        s = _load().get(uid) or {}
    body = {"telegram_user_id": uid,
            "proEnglish": {"said": said or "", "start": start, "state": s.get("state") or {}, **({"audio": audio} if audio else {})}}
    try:
        r = requests.post(f"{SAAS_FUNCTIONS_URL}/espaluz-chat", json=body, timeout=90,
                          headers={"Authorization": f"Bearer {os.environ.get('SUPABASE_ANON_KEY', '')}",
                                   "x-espaluz-bot-secret": os.environ.get("ESPALUZ_BOT_SECRET", "")})
        data = r.json() if r.status_code == 200 else None
    except Exception as e:
        print(f"⚠️ pro english turn failed: {e}", flush=True)
        data = None
    if not data or not data.get("text"):
        BOT.send_message(chat_id, "🔁 Sorry, I missed that. Could you send it again? / No te escuché bien, ¿me lo envías otra vez?")
        return None
    with _lock:
        state = _load()
        if data.get("off"):
            state.pop(uid, None)
        else:
            state[uid] = {"on": True, "last": time.time(), "state": data.get("state") or {}}
        _save(state)
    return data


def _reply(chat_id, data):
    _send(chat_id, data["text"])
    speak = (data.get("speak") or "").strip()
    if not speak or data.get("off"):
        return
    try:
        import espaluz_neural_tts
        path = espaluz_neural_tts.generate_voice_sync(speak, lang="en")
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                BOT.send_voice(chat_id, f, timeout=180)
    except Exception as e:  # noqa: BLE001 - the text already arrived
        print(f"⚠️ pro english voice: {e}", flush=True)


def start(user_id, chat_id):
    print("🇺🇸 pro english ON (Telegram)", flush=True)
    data = _brain(user_id, chat_id, start=True)
    if data:
        _reply(chat_id, data)


def turn(user_id, chat_id, text):
    data = _brain(user_id, chat_id, said=text)
    if data:
        print(f"🇺🇸 pro english turn (Telegram) saved={data.get('saved')} off={bool(data.get('off'))}", flush=True)
        _reply(chat_id, data)


def voice(user_id, chat_id, file_id):
    """Telegram voice notes are OGG/Opus already: transcribed by the bot's own chain, the original goes to Azure."""
    stamp = f"{int(time.time())}_{threading.get_ident()}"
    ogg, mp3 = f"/tmp/pro_en_tg_{stamp}.ogg", f"/tmp/pro_en_tg_{stamp}.mp3"
    try:
        raw = BOT.download_file(BOT.get_file(file_id).file_path)
        with open(ogg, "wb") as f:
            f.write(raw)
        subprocess.run(["ffmpeg", "-y", "-nostdin", "-loglevel", "error", "-i", ogg, mp3], check=True)
        said = TRANSCRIBE(mp3, "English, sometimes Spanish. ", None) or ""
        if not said.strip():
            BOT.send_message(chat_id, "❌ I couldn't hear the words. Try again? / No entendí el audio.")
            return
        print(f"🇺🇸 pro english voice note transcribed ({len(said)} chars)", flush=True)
        data = _brain(user_id, chat_id, said=said, audio={"b64": base64.b64encode(raw).decode(), "mime": "audio/ogg; codecs=opus"})
        if data:
            data["text"] = f"🗣️ _{said.strip()}_\n\n{data['text']}"
            _reply(chat_id, data)
    except Exception as e:
        print(f"⚠️ pro english voice note: {e}", flush=True)
        BOT.send_message(chat_id, "🔁 Sorry, something went wrong with the voice note. Send it again? / Envíalo otra vez, por favor.")
    finally:
        for p in (ogg, mp3):
            try:
                os.remove(p)
            except OSError:
                pass
