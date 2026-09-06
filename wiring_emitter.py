"""
EspaLuz Wiring Emitter — sends events to CTO AIPA Oracle pipeline.

Usage:
    from wiring_emitter import emit_event

    emit_event("user_signup", {"user_id": "123", "trial_end": "2026-04-10"})
    emit_event("payment_received", {"user_id": "123", "email": "user@example.com", "subscription_id": "I-ABC"})
    emit_event("lesson_sent", {"user_id": "123", "lesson_type": "voice", "topic": "banking"})
    emit_event("trial_expired", {"user_id": "123", "days_active": 7})
    emit_event("subscription_cancelled", {"user_id": "123"})

All calls are fire-and-forget with a 2-second timeout.
If CTO AIPA is down, events are silently dropped (no crash).
"""

import os
import threading
import requests
import logging

logger = logging.getLogger(__name__)

# CTO AIPA runs on the same Oracle server at port 3000
CTO_AIPA_WIRING_URL = os.environ.get(
    "CTO_AIPA_WIRING_URL",
    "http://127.0.0.1:3000/wiring/event"
)

# Auto-detect channel from env or filename
AGENT_NAME = os.environ.get("ESPALUZ_AGENT_NAME", "espaluz_telegram")


def emit_event(action: str, data: dict = None, agent: str = None):
    """
    Fire-and-forget event emission to CTO AIPA wiring pipeline.
    Never raises, never blocks longer than 2 seconds.
    """
    def _send():
        try:
            payload = {
                "agent": agent or AGENT_NAME,
                "action": action,
                "data": data or {}
            }
            resp = requests.post(CTO_AIPA_WIRING_URL, json=payload, timeout=2)
            if resp.status_code == 200:
                logger.debug(f"Wiring event sent: {action}")
            else:
                logger.warning(f"Wiring event failed ({resp.status_code}): {action}")
        except Exception as e:
            logger.debug(f"Wiring event skipped (CTO AIPA unreachable): {e}")

    # Run in background thread so it never blocks the bot
    threading.Thread(target=_send, daemon=True).start()
