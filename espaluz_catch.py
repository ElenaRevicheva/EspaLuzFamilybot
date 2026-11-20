"""Catch who a promotion brings (20 Nov 2026).

Elena: "this time when we run promotion, we know exactly who clicks and how to catch this user and what to do with him -
not like last time with YouTube". Audit: cto-aipa docs/espaluz/PROMO_TRACKING_AUDIT_2026-11-20.md.

Twin file: EspaLuzWhatsApp/espaluz_catch.py == EspaLuzFamilybot/espaluz_catch.py (keep them identical).

1. push_arrival(): a person who arrives by a film link becomes a HubSpot [ESPALUZ] deal carrying the film code
   (utm_campaign) and the place it was posted (utm_content: fb / ig / yt / g<n> = a Facebook group). Reuses the CTO AIPA
   /api/crm-event door the bots already use for trials. Fire-and-forget: never slows or blocks a reply.
2. android(): the Google Play beta door. A short message that starts with ANDROID gets the 3 tester steps and is asked
   for the Google account it will use; that address joins play_testers (kids-memory beta_tester) with free use until
   31 Dec. Private - nobody has to post an email in a public comment.
"""
import json
import logging
import os
import re
import threading
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "android_beta.json")
KIDS_MEMORY = "https://euyidvolwqmzijkfrplh.supabase.co/functions/v1/kids-memory"
WAIT_SECONDS = 2 * 24 * 3600  # the email may come a day later

ANDROID_RE = re.compile(r"^\s*(android|andriod|андроид)\b", re.I)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,24}")
FILM_RE = re.compile(r"\b(f\d{8}[0-9a-f]{4})[-_](fb|ig|yt|g\d{1,3})\b")

GROUP = "https://groups.google.com/g/espaluz-testers/about"
OPT_IN = "https://play.google.com/apps/testing/lat.espaluz.app"
INSTALL = "https://play.google.com/store/apps/details?id=lat.espaluz.app"

STEPS = (
    "📱 ¡Genial! Tu cupo en la beta de EspaLuz para Android · Great, your EspaLuz Android beta spot:\n\n"
    f"1) Únete al grupo · Join the group: {GROUP}\n"
    f"2) Toca \"Convertirse en tester\" · Tap \"Become a tester\": {OPT_IN}\n"
    f"3) Instala · Install: {INSTALL}\n\n"
    "Usa la MISMA cuenta de Google en los 3 pasos · Use the SAME Google account in all 3 steps.\n\n"
    "✉️ Ahora escríbeme esa dirección de Google (tu Gmail), y tu familia usa EspaLuz GRATIS hasta el 31 de diciembre. "
    "Now send me that Google address (your Gmail), and your family uses EspaLuz FREE until 31 December."
)
DONE = (
    "✅ ¡Listo! {email} usa EspaLuz gratis hasta el 31 de diciembre: entra en la app con esa cuenta. "
    "Done! {email} uses EspaLuz free until 31 December: sign in to the app with that account.\n"
    "Cuéntame todo lo que te parezca confuso o roto · Tell me anything that feels confusing or broken. 💛"
)
ALREADY = (
    "✅ {email} ya está en la beta, gratis hasta el 31 de diciembre · is already in the beta, free until 31 December. "
    "Entra en la app con esa cuenta · Sign in to the app with that account."
)
FAILED = ("Uy, no pude guardarlo ahora · I couldn't save it right now. "
          "Escríbelo otra vez en un minuto · Please send it again in a minute.")


def _load():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001 - no file yet
        return {}


def _save(data):
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, STATE)


def _key(platform, who):
    return f"{platform}:{who}"


def push_arrival(platform, who, film, tag, first_text=""):
    """Film arrival -> HubSpot deal with the film code. Never raises, never blocks."""
    secret = os.getenv("OUTREACH_SECRET", "").strip()
    if not secret:
        return
    base = (os.getenv("CTO_AIPA_WEBHOOK_URL") or "https://webhook.aideazz.xyz/cto").rstrip("/")
    where = {"fb": "Facebook", "ig": "Instagram", "yt": "YouTube"}.get(tag, f"Facebook group {tag[1:]}" if tag.startswith("g") else tag)

    def work():
        try:
            payload = {
                "source": f"espaluz_{platform}", "type": "film_arrival", "pipeline": "client",
                "name": str(who), "userId": str(who),
                "context": f"EspaLuz {platform} | arrived from film {film} on {where} | first message: {(first_text or '')[:120]}",
                "utm_campaign": film, "utm_content": tag, "signalStrength": "high",
            }
            r = requests.post(f"{base}/api/crm-event", json=payload, timeout=8,
                              headers={"Authorization": f"Bearer {secret}"})
            print(f"🎯 film arrival -> HubSpot {film}-{tag} channel={platform} status={r.status_code}", flush=True)
        except Exception as e:  # noqa: BLE001
            logging.warning(f"film arrival push non-fatal: {str(e)[:160]}")
    threading.Thread(target=work, daemon=True).start()


def android(platform, who, text, ident):
    """Returns the reply to send, or None when this message is not part of the Android beta door.

    ident = the bot's own id fields for kids-memory (telegram_user_id / whatsapp_user_id)."""
    text = text or ""
    state = _load()
    key = _key(platform, who)
    waiting = state.get(key)
    if ANDROID_RE.match(text) and len(text) <= 80:
        film = FILM_RE.search(text)
        state[key] = {"t": time.time(), "film": f"{film.group(1)}-{film.group(2)}" if film else ""}
        _save(state)
        print(f"📱 android beta asked channel={platform} film={state[key]['film'] or '-'}", flush=True)
        return STEPS
    if not waiting or time.time() - waiting.get("t", 0) > WAIT_SECONDS:
        return None
    found = EMAIL_RE.search(text)
    if not found:
        return None
    email = found.group(0).lower()
    try:
        r = requests.post(KIDS_MEMORY, timeout=20,
                          json={"mode": "beta_tester", "email": email, "platform": platform, "film": waiting.get("film", ""), **ident},
                          headers={"x-espaluz-bot-secret": os.getenv("ESPALUZ_BOT_SECRET", ""), "Content-Type": "application/json",
                                   "Authorization": f"Bearer {os.getenv('SUPABASE_ANON_KEY', '')}"})
        got = r.json() if r.status_code == 200 else {}
    except Exception as e:  # noqa: BLE001
        logging.warning(f"android beta non-fatal: {str(e)[:160]}")
        got = {}
    if not got.get("ok"):
        return FAILED
    state.pop(key, None)
    _save(state)
    print(f"📱 android beta tester saved channel={platform} already={bool(got.get('already'))}", flush=True)
    return (ALREADY if got.get("already") else DONE).format(email=email)
