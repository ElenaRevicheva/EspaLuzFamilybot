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

RESTING = ("Estoy descansando un ratito 😴 Tu mensaje y tu historial están guardados; escríbeme de nuevo en un rato.\n\n"
           "I'm resting for a little while. Your message and history are saved; write to me again soon.")
RESTING_SHORT = "Estoy descansando un ratito. Escríbeme de nuevo en un rato."

LIMIT_REACHED = ("🌙 Por hoy ya usamos todas las respuestas gratis. ¡Mañana seguimos! Con la suscripción no hay límite "
                 "diario.\n\nThat's all the free replies for today. We continue tomorrow! With a subscription there is "
                 "no daily limit.")


def _limit() -> int:
    try:
        return max(1, int(os.environ.get("FREE_DAILY_REPLIES", "30")))
    except ValueError:
        return 30


def _panama_day() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(time.time() - 5 * 3600))  # UTC-5, no DST


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
