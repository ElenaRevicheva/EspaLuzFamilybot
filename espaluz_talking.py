"""The real talking EspaLuz on Telegram and WhatsApp. Identical file in both bots.

6 Nov 2026 (Elena: the old loop after every reply is "the past season"; "not noisy"). Text and voice go on every reply as
before. The clip comes only at a moment: the first reply of the day or a low mood (at most 2 a day), or when the person
asks by typing "video". Paying families only, up to 30 a month; everyone else gets the pre-made hello once, which costs
nothing. The clip is made by the same door as the web chat (generate-video), with the free Emma voice made here.
Every failure is silent: the person already has the text and the voice.
"""
import asyncio
import base64
import logging
import os
import re
import sys
import tempfile
import threading
import time

import psycopg2
import requests

DOOR = "https://euyidvolwqmzijkfrplh.supabase.co/functions/v1/generate-video"
VOICE = "en-US-EmmaMultilingualNeural"
MONTHLY_CAP = 30
DAILY_MOMENTS = 2
MAX_CHARS = 450
ASK_WORDS = {"video", "ver video", "ver a espaluz", "see espaluz", "video please", "video por favor"}
LOW_MOODS = {"sad", "frustrated", "confused", "nervous", "homesick", "overwhelmed", "anxious", "worried", "stressed", "lonely", "tired"}
HERE = os.path.dirname(os.path.abspath(__file__))
_last_words = {}


def _db():
    return psycopg2.connect(os.getenv("ESPALUZ_UNIFIED_DB_URL") or os.getenv("DATABASE_URL_UNIFIED"), connect_timeout=5)


def _count(platform, who, kind, since_sql):
    with _db() as c, c.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM event_log WHERE event_type=%s AND platform=%s AND event_data->>'who'=%s AND created_at >= {since_sql}",
                    (kind, platform, who))
        return cur.fetchone()[0]


def _note(platform, who, kind, reason):
    with _db() as c, c.cursor() as cur:
        cur.execute("INSERT INTO event_log (event_type, platform, event_data, created_at) VALUES (%s, %s, jsonb_build_object('who', %s::text, 'reason', %s::text), NOW())",
                    (kind, platform, who, reason))


def _is_paying(platform, who):
    try:
        fb = os.getenv("ESPALUZ_FAMILYBOT_DIR", os.path.abspath(os.path.join(HERE, "..", "EspaLuzFamilybot")))
        if fb not in sys.path:
            sys.path.insert(0, fb)
        import espaluz_payment_truth as truth
        row = truth.access(telegram_id=who) if platform == "telegram" else truth.access(whatsapp_id=who)
        return bool(row and row.get("paid"))
    except Exception as e:  # noqa: BLE001 - unknown means no spend
        logging.warning(f"talking: payment check failed: {str(e)[:120]}")
        return False


def _emma(text):
    import edge_tts
    path = tempfile.mktemp(suffix=".mp3")
    asyncio.run(edge_tts.Communicate(text, VOICE, rate="+2%", pitch="+6Hz").save(path))
    with open(path, "rb") as f:
        data = f.read()
    os.remove(path)
    return data


def _door(body):
    r = requests.post(DOOR, json=body, timeout=90, headers={
        "x-espaluz-bot-secret": os.getenv("ESPALUZ_BOT_SECRET", ""), "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('SUPABASE_ANON_KEY', '')}"})
    return r.json() if r.status_code == 200 else {}


def make_clip(text, reason, platform):
    """The path of a new mp4, or None."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) > MAX_CHARS:
        cut = text[:MAX_CHARS]
        end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
        text = cut[:end + 1] if end > 80 else cut
    if len(text) < 2:
        return None
    started = _door({"mode": "real", "reason": reason, "platform": platform, "chars": len(text),
                     "audioBase64": base64.b64encode(_emma(text)).decode()})
    task = started.get("taskId")
    if not task:
        print(f"🎬 [talking] no clip: {started.get('reason', 'door')}", flush=True)
        return None
    until = time.time() + 150
    while time.time() < until:
        time.sleep(5)
        st = _door({"mode": "real_status", "taskId": task})
        if st.get("status") == "done" and st.get("url"):
            video = requests.get(st["url"], timeout=120)
            video.raise_for_status()
            path = tempfile.mktemp(suffix=".mp4")
            with open(path, "wb") as f:
                f.write(video.content)
            return path
        if not st.get("real"):
            break
    print("🎬 [talking] no clip: not finished", flush=True)
    return None


LINE_RULES = ("You write what EspaLuz, a warm friend of this family, says aloud in a short personal video. Spanish first, then the same in "
              "English, under 45 words in all, plain speech, no emojis, no labels, no quotes. NEVER repeat the reply they just read: bring something it does "
              "not contain. Never invent anything: use only the NOTES and the REPLY. Never state a price, a date or a name that is not there. Warm and light. Never mention marital status, money, health or hardship. ")
LINE_MOMENT = {
    "first_today": "Moment: first talk of the day. Ask warmly about ONE thing from the NOTES, like a friend who remembered.",
    "low_mood": "Moment: they sound low. One calm, personal line that uses ONE thing from the NOTES, then one kind thought. No advice list.",
    "asked": "Moment: they asked to see you. Take the single most useful Spanish phrase from the REPLY. Say it slowly, say it again, then what it means in English and when to use it.",
}


def _words(text):
    import unicodedata
    plain = "".join(c for c in unicodedata.normalize("NFD", (text or "").lower()) if unicodedata.category(c) != "Mn")
    return set(re.findall(r"[a-zñ]{3,}", plain))


def _repeats(line, reply):
    mine, other = _words(line), _words(reply)
    return not mine or len(mine & other) / len(mine) > 0.7


def special_line(platform, who, reason, reply):
    """A clip brings something the message did not (Elena, 6 Nov 2026). No true note, or only a repeat: no clip."""
    from espaluz_memory import EspaLuzMemory
    from llm_chain import complete
    mem = EspaLuzMemory(platform=platform, platform_user_id=who)
    notes = [str(f) for f in mem.family_notes().get("facts", [])]
    own = [str(m.get("content", "")) for m in mem.get_user_memories(mem.user_id, limit=12)] if mem.user_id else []
    notes = [n for n in dict.fromkeys(notes + own) if not re.search(r"spouse|single parent|divorc|widow|money|debt|\[object", n, re.I)][:12]
    if reason != "asked" and not notes:
        return ""
    prompt = "NOTES:\n" + ("\n".join(f"- {n}" for n in notes) or "none") + f"\nREPLY THEY JUST READ:\n{(reply or '')[:1200]}"
    line, _err = complete(LINE_RULES + LINE_MOMENT.get(reason, LINE_MOMENT["asked"]), prompt, max_tokens=220, order=("gemini", "groq", "grok", "openai"))
    line = re.sub(r"\s+", " ", (line or "").replace("*", "")).strip().strip('"')
    if not line or _repeats(line, reply):
        print(f"🎬 [talking] nothing special to say reason={reason}", flush=True)
        return ""
    return line


def _clip_and_send(platform, who, text, reason, send_file):
    try:
        line = special_line(platform, who, reason, text)
        path = make_clip(line, reason, platform) if line else None
        if not path:
            return
        ok = send_file(path)
        if ok is not False:
            _note(platform, who, "talking_video", reason)
        print(f"🎬 [talking] clip {'sent' if ok is not False else 'not sent'} reason={reason} channel={platform}", flush=True)
        # WhatsApp hosts the file for Twilio to fetch, so it is left for the temp cleaner there.
        if platform == "telegram":
            try:
                os.remove(path)
            except OSError:
                pass
    except Exception as e:  # noqa: BLE001
        logging.warning(f"talking: clip non-fatal: {str(e)[:160]}")


def _decide(platform, who, text, mood, send_file):
    try:
        if _is_paying(platform, who):
            if _count(platform, who, "talking_video", "date_trunc('month', NOW())") >= MONTHLY_CAP:
                return
            today = _count(platform, who, "talking_video", "date_trunc('day', NOW())")
            if today >= DAILY_MOMENTS:
                return
            low = str(mood or "").strip().lower() in LOW_MOODS
            if low or today == 0:
                _clip_and_send(platform, who, text, "low_mood" if low else "first_today", send_file)
            return
        if _count(platform, who, "talking_hello", "'2000-01-01'::timestamp") == 0:
            spanish = bool(re.search(r"[áéíóúñ¿¡]|\b(hola|que|para|estoy|gracias)\b", text or "", re.I))
            path = os.path.join(HERE, f"hello-chat-{'es' if spanish else 'en'}.mp4")
            if os.path.exists(path) and send_file(path) is not False:
                _note(platform, who, "talking_hello", "hello")
                print(f"🎬 [talking] pre-made hello sent channel={platform}", flush=True)
    except Exception as e:  # noqa: BLE001
        logging.warning(f"talking: decision non-fatal: {str(e)[:160]}")


def on_reply(platform, who, text, mood, send_file):
    """After a grown-up reply. Never blocks the reply."""
    who = str(who)
    _last_words[(platform, who)] = text
    threading.Thread(target=_decide, args=(platform, who, text, mood, send_file), daemon=True).start()


def is_ask(text):
    return (text or "").strip().lower().rstrip("!.") in ASK_WORDS


def on_ask(platform, who, send_file, send_text):
    """The person typed "video"."""
    who = str(who)

    def work():
        try:
            if not _is_paying(platform, who):
                send_text("Mi video con cada respuesta es para familias suscritas. Aquí sigo contigo por texto y voz. / "
                          "Video replies are for subscribed families. I'm still here by text and voice.")
                return
            if _count(platform, who, "talking_video", "date_trunc('month', NOW())") >= MONTHLY_CAP:
                send_text("Ya usamos los videos de este mes. Aquí sigo por texto y voz. / This month's videos are used up. I'm still here by text and voice.")
                return
            words = _last_words.get((platform, who))
            if not words:
                send_text("Cuéntame algo primero y te respondo en video. / Tell me something first and I'll answer on video.")
                return
            send_text("Un momento, ya vengo. / One moment, I'm coming.")
            _clip_and_send(platform, who, words, "asked", send_file)
        except Exception as e:  # noqa: BLE001
            logging.warning(f"talking: ask non-fatal: {str(e)[:160]}")
    threading.Thread(target=work, daemon=True).start()
