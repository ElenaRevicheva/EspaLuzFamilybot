"""
Never silence, and free use that cannot starve the paying families (4 Nov 2026, Phase 0 step 4 of
cto-aipa docs/espaluz/MODEL_COST_STRATEGY_2026-11-03.md). TWIN: EspaLuzWhatsApp/fair_use.py — change one, change both.

Measured 3 Nov: Gemini answers 402, Groq's free daily tokens are gone by evening, the web leans on one provider. At launch
more families arrive at once, so two rules, both in code:

1. A trial/free user gets FREE_DAILY_REPLIES tutor replies per Panama day (default 30). Paying families have no cap —
   any access reason that is not a trial counts as paying, so an unknown reason never locks out a payer.
2. When every provider failed, the family gets a kind resting message — never an error, never nothing — and one
   "[chain-out]" line goes to the journal. cto-aipa scripts/espaluz-chain-alert.py turns that line into a Telegram
   message to Elena, so she hears about it before a family does.

Nothing here may raise: a broken counter must never cost a family their reply.
"""
import json
import os
import threading
import time

FREE_REASONS = {"trial", "new_trial", "existing_user_grace"}
_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fair_use_counts.json")
_LOCK = threading.Lock()

# When every provider is out, the family is told WHEN to come back (Elena, 4 Nov 2026: "en un rato" is not an answer).
# The free daily quotas the chain lives on reset at 00:00 UTC = 7:00 pm Panama, so that is the promised time, with the
# date. The trial counter resets at Panama midnight. These names are computed on every read (module __getattr__ below),
# so callers keep writing fair_use.RESTING and always get today's date.
_DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
          "noviembre", "diciembre"]
_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
           "November", "December"]
_PANAMA = 5 * 3600  # UTC-5, no DST


def _day_words(t: float):
    """(es, en) words for the Panama calendar day of UTC epoch t: 'jueves 5 de noviembre' / 'Thursday 5 November'."""
    d = time.gmtime(t - _PANAMA)
    return (f"{_DIAS[d.tm_wday]} {d.tm_mday} de {_MESES[d.tm_mon - 1]}",
            f"{_DAYS[d.tm_wday]} {d.tm_mday} {_MONTHS[d.tm_mon - 1]}")


def back_at(now=None):
    """(es, en) 'when to try again': the next 00:00 UTC, said as 7:00 pm Panama today or tomorrow, with the date."""
    now = time.time() if now is None else now
    reset = (int(now) // 86400 + 1) * 86400
    es_day, en_day = _day_words(reset)
    today = time.gmtime(now - _PANAMA).tm_yday == time.gmtime(reset - _PANAMA).tm_yday
    return ((f"{'hoy' if today else 'mañana'}, {es_day}, a partir de las 7:00 p. m. (hora de Panamá)"),
            (f"{'today' if today else 'tomorrow'}, {en_day}, from 7:00 pm Panama time"))


def _texts(now=None):
    now = time.time() if now is None else now
    es_at, en_at = back_at(now)
    es_tom, en_tom = _day_words(now + 86400)
    return {
        "RESTING": (f"Estoy descansando un ratito 😴 Tu mensaje y tu historial están guardados. Escríbeme de nuevo "
                    f"{es_at}.\n\nI'm resting for a while. Your message and history are saved. Write to me again "
                    f"{en_at}."),
        "RESTING_SHORT": f"Estoy descansando. Escríbeme de nuevo {es_at}.",
        "LIMIT_REACHED": (f"🌙 Por hoy ya usamos todas las respuestas gratis. Seguimos mañana, {es_tom}, desde las "
                          f"12:00 a. m. (hora de Panamá). Con la suscripción no hay límite diario.\n\nThat's all the "
                          f"free replies for today. We continue tomorrow, {en_tom}, from midnight Panama time. With a "
                          f"subscription there is no daily limit."),
    }


def __getattr__(name):  # PEP 562: fair_use.RESTING etc. are built fresh, with the current date
    texts = _texts()
    if name in texts:
        return texts[name]
    raise AttributeError(name)


def _limit() -> int:
    try:
        return max(1, int(os.environ.get("FREE_DAILY_REPLIES", "30")))
    except ValueError:
        return 30


def _panama_day() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(time.time() - _PANAMA))


def over_daily_limit(user_id, reason) -> bool:
    """Count one tutor reply for a trial user; True when they are past today's free replies. Payers: always False."""
    try:
        if str(reason or "") not in FREE_REASONS:
            return False
        day, uid = _panama_day(), str(user_id)
        with _LOCK:
            try:
                with open(_FILE, encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, ValueError):
                data = {}
            today = data.get(day, {}) if isinstance(data.get(day), dict) else {}
            today[uid] = int(today.get(uid, 0)) + 1
            with open(_FILE, "w", encoding="utf-8") as f:
                json.dump({day: today}, f)  # only today is kept
        if today[uid] > _limit():
            print(f"[fair-use] limit reached user={uid[-4:]} reason={reason} n={today[uid]}", flush=True)
            return True
        return False
    except Exception:  # noqa: BLE001
        return False


def chain_out(channel: str, errors="") -> None:
    """One line for the alert watcher: every provider failed and the family got the resting message."""
    try:
        print(f"[chain-out] ch={channel} {str(errors)[:300]}", flush=True)
    except Exception:  # noqa: BLE001
        pass
