"""The real talking EspaLuz on Telegram and WhatsApp. Identical file in both bots.

6 Nov 2026 (Elena: the old loop after every reply is "the past season"; "not noisy"). Text and voice go on every reply as
before. Her clip is a rare surprise (Elena: "something truly useful, practically useful for a user, as well as warm and personal",
never "how do you feel today"): only when what she remembers lets her bring something practical, at most one in 3 days,
and she stays silent otherwise. Or when the person asks by typing "video". Paying families only, up to 30 a month; everyone else gets
the pre-made hello once, which costs nothing. The clip is made by the same door as the web chat (generate-video), with the free Emma voice made here.
Every failure is silent: the person already has the text and the voice.
"""
import asyncio
import base64
import hashlib
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
SURPRISE_EVERY_DAYS = 3  # Elena, 6 Nov 2026: usefulness decides; this only stops a run of visits
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


def _surprises(platform, who, days):
    """Clips she chose to send in the last N days; a clip the person asked for does not count."""
    with _db() as c, c.cursor() as cur:
        cur.execute("SELECT count(*) FROM event_log WHERE event_type='talking_video' AND platform=%s AND event_data->>'who'=%s "
                    "AND coalesce(event_data->>'reason','') <> 'asked' AND created_at >= NOW() - (%s * INTERVAL '1 day')", (platform, who, days))
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
        if row and row.get("paid"):
            return True
        # A family linked to the web that pays on another channel is paying here too.
        from espaluz_memory import EspaLuzMemory
        probe = EspaLuzMemory.__new__(EspaLuzMemory)
        probe.platform, probe.platform_user_id = platform, who
        return bool(probe._family_call("facts_get").get("family_paying"))
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
              "not contain. Never invent anything: use only the NOTES and the REPLY. Never state a price, a date or a name that is not there. Never mention marital status, money, health or hardship. "
              "Speak to this one grown-up, warm and personal, like a friend who knows their life. Bring ONE concrete, practically useful thing tied to a NOTE: what to say, what to bring, who to ask, or the exact Spanish phrase for what is coming up, and why it helps. Never ask how they feel, never offer psychological support or encouragement, never describe their feelings, never praise. Use only facts in the NOTES, no guessed details. You speak to the grown-up named in TALKING TO, by name at most once. Talk ABOUT a child, never TO a child. Never state a rule, a policy or what a school or office will do. Write normal words, never spaced-out letters. If you cannot be really useful, reply exactly NONE. ")
LINE_MOMENT = {
    "remembered": "Moment: a surprise visit. Only if a NOTE names something coming up or just past, give the one thing that will help them with it. Otherwise reply NONE.",
    "low_mood": "Moment: they are having a hard moment. Do not talk about it. Take one practical thing off their plate, tied to a NOTE: a ready sentence or the next small step.",
    "long_road": "Moment: the long road. From the NOTES, the next practical step or Spanish phrase this family is ready for now, and why now.",
    "asked": "Moment: they asked to see you. Take the single most useful Spanish phrase from the REPLY. Say it once with commas between small groups of words so it sounds slow, say it again normally, then what it means in English and when to use it.",
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
    family = mem.family_notes()
    talking_to = mem._recognize(family) if family else ""
    talking_to = talking_to or (str(mem.user.display_name).split()[0] if mem.user and mem.user.display_name else "the parent")
    notes = [str(f) for f in family.get("facts", [])]
    own = [str(m.get("content", "")) for m in mem.get_user_memories(mem.user_id, limit=12)] if mem.user_id else []
    notes = [n for n in dict.fromkeys(notes + own) if not re.search(r"spouse|single parent|divorc|widow|money|debt|\[object", n, re.I)][:12]
    if reason != "asked" and not notes:
        return ""
    if reason == "long_road" and len(notes) < 5:
        return ""
    prompt = f"TODAY: {time.strftime('%A %Y-%m-%d')}\nTALKING TO: {talking_to}\nNOTES:\n" + ("\n".join(f"- {n}" for n in notes) or "none") + f"\nREPLY THEY JUST READ:\n{(reply or '')[:1200]}"
    line, _err = complete(LINE_RULES + LINE_MOMENT.get(reason, LINE_MOMENT["asked"]), prompt, max_tokens=220, order=("gemini", "groq", "grok", "openai"))
    line = re.sub(r"\s+", " ", (line or "").replace("*", "")).strip().strip('"')
    if reason == "asked":  # typing "video" always gets a clip: the phrase comes from the reply, so overlap is expected
        return line if line and not line.upper().startswith("NONE") else (reply or "")[:300]
    if not line or line.upper().startswith("NONE") or _repeats(line, reply):
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
            if _surprises(platform, who, SURPRISE_EVERY_DAYS) > 0:
                return
            low = str(mood or "").strip().lower() in LOW_MOODS
            reason = "low_mood" if low else ("long_road" if _surprises(platform, who, 30) == 0 and _count(platform, who, "talking_video", "'2000-01-01'::timestamp") > 0 else "remembered")
            _clip_and_send(platform, who, text, reason, send_file)
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


def _plain(text):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", (text or "").lower())).strip()


def is_ask(text):
    return _plain(text) in ASK_WORDS


def on_ask(platform, who, send_file, send_text):
    """The person typed "video"."""
    who = str(who)

    def work():
        try:
            if not _is_paying(platform, who):
                # A tap always delivers something: the pre-made hello costs nothing.
                hello = os.path.join(HERE, f"hello-chat-{'es' if platform == 'whatsapp' else 'en'}.mp4")
                if os.path.exists(hello):
                    send_file(hello)
                    print(f"🎬 [talking] pre-made hello on tap channel={platform}", flush=True)
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


# ---------- One tap into the classroom (6 Nov 2026) ----------
# Elena's policy is unchanged: 14 free days, no sign-up, then subscribe. The classroom sits inside the same 14 days.
CLASS_WORDS = {"clase", "la clase", "class", "classroom", "pere y titi", "pere and titi", "clase class", "kids classroom", "kids class"}
CHILD_TALK = re.compile(r"\b(mi hij[oa]|mis hij[oa]s|mi peque|my (daughter|son|kid|child)|my kids|mi ni[nñ][oa]|escuela|colegio|school)\b", re.I)


def is_class_ask(text):
    return _plain(text) in CLASS_WORDS


def _class_link(platform, who, trial_status):
    """A signed-in link, or None when this person has no paid time and no running trial."""
    paid = _is_paying(platform, who)
    until = None
    status = trial_status or {}
    if status.get("is_active") and status.get("trial_end"):
        until = str(status["trial_end"])
        if "+" not in until and not until.endswith("Z"):
            until += "Z"
    if not paid and not until:
        return None
    ident = {"telegram_user_id": who} if platform == "telegram" else {"whatsapp_user_id": "wa_" + hashlib.sha256(
        ("espaluz-wa:" + re.sub(r"\D", "", who)).encode()).hexdigest()[:32]}
    r = requests.post(DOOR.replace("generate-video", "kids-memory"), timeout=20,
                      json={"mode": "classroom_link", "trial_until": until, "paid": paid, **ident},
                      headers={"x-espaluz-bot-secret": os.getenv("ESPALUZ_BOT_SECRET", ""), "Content-Type": "application/json",
                               "Authorization": f"Bearer {os.getenv('SUPABASE_ANON_KEY', '')}"})
    got = r.json() if r.status_code == 200 else {}
    return got.get("url")


def send_class_link(platform, who, trial_status, send_text, offer=False):
    """Asked for class, or (offer=True) the person just mentioned a child or school: once only, and never blocks a reply."""
    who = str(who)

    def work():
        try:
            if offer and _count(platform, who, "classroom_offer", "'2000-01-01'::timestamp") > 0:
                return
            url = _class_link(platform, who, trial_status)
            if not url:
                if not offer:
                    send_text("Las clases de Pere y Titi siguen con una suscripción. / Pere and Titi's classes continue with a subscription.")
                return
            lead = ("Por cierto, Pere y Titi pueden darle una clasecita a tu peque: diez minutos en español e inglés. / By the way, Pere and Titi "
                    "can give your child a little class: ten minutes in Spanish and English.\n" if offer else "")
            send_text(lead + f"Un toque y entras, sin contraseña. / One tap and you're in, no password.\n{url}\n"
                             "Si el enlace caduca, escribe «clase». / If the link expires, type \"class\".")
            _note(platform, who, "classroom_offer", "offer" if offer else "asked")
            print(f"🏫 classroom link sent channel={platform} offer={offer}", flush=True)
        except Exception as e:  # noqa: BLE001
            logging.warning(f"classroom link non-fatal: {str(e)[:160]}")
    threading.Thread(target=work, daemon=True).start()


# ---------- Buttons (6 Nov 2026, Elena: "nobody will type video") ----------
# Both labels come back as plain message text, so is_ask and is_class_ask handle a tap exactly like typing.
VIDEO_LABEL = "🎬 Ver a EspaLuz"
CLASS_LABEL = "🏫 Kids Classroom"  # Elena: "Class" alone reads as a class for the grown-up
BUTTON_TEXT = "Cuando quieras, toca aquí. / Whenever you like, tap here."
BUTTONS_EVENT = "buttons_shown_v2"  # new name so people who saw the old label get the new one once
WA_BUTTON_EVERY_HOURS = 6  # each WhatsApp message costs a little, and a button after every reply would be noise
_wa_content_sid = None


def telegram_buttons(bot, chat_id):
    """A keyboard that stays under the chat: always tappable, sent once per person."""
    who = str(chat_id)

    def work():
        try:
            if _count("telegram", who, BUTTONS_EVENT, "'2000-01-01'::timestamp") > 0:
                return
            from telebot import types
            keys = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keys.is_persistent = True
            keys.add(types.KeyboardButton(VIDEO_LABEL), types.KeyboardButton(CLASS_LABEL))
            bot.send_message(chat_id, BUTTON_TEXT, reply_markup=keys)
            _note("telegram", who, BUTTONS_EVENT, "keyboard")
            print("🔘 buttons shown channel=telegram", flush=True)
        except Exception as e:  # noqa: BLE001
            logging.warning(f"telegram buttons non-fatal: {str(e)[:160]}")
    threading.Thread(target=work, daemon=True).start()


def _wa_template(sid, token):
    """The quick-reply template, made once. Within a 24-hour conversation it needs no Meta approval."""
    global _wa_content_sid
    if _wa_content_sid:
        return _wa_content_sid
    path = os.path.join(HERE, ".wa_buttons_content_sid_v2")
    if os.path.exists(path):
        _wa_content_sid = open(path).read().strip()
        return _wa_content_sid
    r = requests.post("https://content.twilio.com/v1/Content", auth=(sid, token), timeout=20, json={
        "friendly_name": "espaluz_buttons_v2", "language": "es", "types": {"twilio/quick-reply": {"body": BUTTON_TEXT, "actions": [
            {"title": VIDEO_LABEL, "id": "video"}, {"title": CLASS_LABEL, "id": "clase"}]}, "twilio/text": {"body": BUTTON_TEXT}}})
    r.raise_for_status()
    _wa_content_sid = r.json()["sid"]
    with open(path, "w") as f:
        f.write(_wa_content_sid)
    return _wa_content_sid


def whatsapp_buttons(user_id, sender):
    """Quick-reply buttons after a reply, at most once in 6 hours per person."""
    who = str(user_id)

    def work():
        try:
            with _db() as c, c.cursor() as cur:
                cur.execute("SELECT count(*) FROM event_log WHERE event_type=%s AND platform='whatsapp' AND event_data->>'who'=%s "
                            "AND created_at >= NOW() - (%s * INTERVAL '1 hour')", (BUTTONS_EVENT, who, WA_BUTTON_EVERY_HOURS))
                if cur.fetchone()[0] > 0:
                    return
            sid, token = os.getenv("TWILIO_ACCOUNT_SID", ""), os.getenv("TWILIO_AUTH_TOKEN", "")
            to = who if who.startswith("+") else f"+{who}"
            r = requests.post(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json", auth=(sid, token), timeout=20,
                              data={"From": sender, "To": f"whatsapp:{to}", "ContentSid": _wa_template(sid, token)})
            if r.status_code == 201:
                _note("whatsapp", who, BUTTONS_EVENT, "quick_reply")
                print("🔘 buttons shown channel=whatsapp", flush=True)
            else:
                logging.warning(f"whatsapp buttons refused: {r.status_code} {r.text[:200]}")
        except Exception as e:  # noqa: BLE001
            logging.warning(f"whatsapp buttons non-fatal: {str(e)[:160]}")
    threading.Thread(target=work, daemon=True).start()
