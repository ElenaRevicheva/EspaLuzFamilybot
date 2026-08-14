#!/usr/bin/env python3
"""
EspaLuz PagueloFacil — one-time monthly payments (no subscriptions).

Supports Telegram (numeric / TG: id) and WhatsApp (WA: phone) via PARM_1 prefix.
Docs: https://developers.paguelofacil.com/guias/enlace-de-pago
Webhook: https://webhook.aideazz.xyz/paguelofacil-webhook (paypal_webhook_server.py)
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

load_dotenv()

PAGUELOFACIL_CCLW = os.getenv("PAGUELOFACIL_CCLW", "").strip()
PAGUELOFACIL_SANDBOX = os.getenv("PAGUELOFACIL_SANDBOX", "false").lower() in ("1", "true", "yes")
PAGUELOFACIL_AMOUNT = os.getenv("PAGUELOFACIL_AMOUNT", "11.00").strip()
PAGUELOFACIL_AMOUNT_WA = os.getenv("PAGUELOFACIL_AMOUNT_WA", PAGUELOFACIL_AMOUNT).strip()
PAGUELOFACIL_ACCESS_DAYS = int(os.getenv("PAGUELOFACIL_ACCESS_DAYS", "30"))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
PAGUELOFACIL_WA_NOTIFY_URL = os.getenv(
    "PAGUELOFACIL_WA_NOTIFY_URL",
    "http://127.0.0.1:8081/internal/paguelofacil-grant",
).strip()
INTERNAL_WEBHOOK_SECRET = os.getenv("INTERNAL_WEBHOOK_SECRET", "").strip()

PLATFORM_TELEGRAM = "telegram"
PLATFORM_WHATSAPP = "whatsapp"

LINK_URL = (
    "https://sandbox.paguelofacil.com/LinkDeamon.cfm"
    if PAGUELOFACIL_SANDBOX
    else "https://secure.paguelofacil.com/LinkDeamon.cfm"
)

PAYMENTS_FILE = os.getenv("PAGUELOFACIL_PAYMENTS_FILE", "paguelofacil_payments.json")
TG_USER_RE = re.compile(r"(?:TG[:\s-]|telegram[:\s-])(\d{5,20})", re.I)
WA_USER_RE = re.compile(r"(?:WA[:\s-])(\+?\d{8,15})", re.I)


def _base_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _payments_path() -> str:
    path = PAYMENTS_FILE
    if not os.path.isabs(path):
        path = os.path.join(_base_dir(), path)
    return path


def normalize_whatsapp_id(raw: str) -> str:
    """Match EspaLuz WhatsApp bridge format: +50761968038 (E.164 with +)."""
    s = str(raw or "").strip().replace("whatsapp:", "")
    if not s:
        return s
    digits = "".join(c for c in s if c.isdigit())
    if not digits:
        return s
    return s if s.startswith("+") else f"+{digits}"


def _empty_store() -> Dict[str, Any]:
    return {"orders": {}, "users": {}, "processed": {}}


def _durable():
    """The Postgres mirror, or None if unavailable. Never raises — payments
    must keep working whether or not the safety net is reachable."""
    try:
        import espaluz_pf_durable as _d  # noqa: WPS433

        return _d
    except Exception:  # noqa: BLE001
        return None


def _restore_from_durable(path: str, reason: str) -> Optional[Dict[str, Any]]:
    """
    The payment file is gone or unreadable. Before accepting "nobody ever
    paid" — which is what an empty store means to every caller — ask Postgres.

    Returns the recovered store (and rewrites the file) or None.
    """
    d = _durable()
    if d is None:
        return None
    try:
        doc = d.latest()
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(doc, dict) or not (doc.get("users") or doc.get("processed")):
        return None
    doc.setdefault("orders", {})
    doc.setdefault("users", {})
    doc.setdefault("processed", {})
    logging.warning(
        "PagueloFacil store %s (%s) — RESTORED from Postgres: %d users, %d processed payments",
        path, reason, len(doc["users"]), len(doc["processed"]),
    )
    try:
        _write_store_file(path, doc)
    except OSError:
        pass
    return doc


def _quarantine(path: str) -> None:
    """Preserve an unreadable payment file instead of letting the next save
    silently overwrite it. Money records are never discarded, only set aside."""
    try:
        import time

        os.rename(path, f"{path}.corrupt.{time.strftime('%Y%m%d%H%M%S')}")
    except OSError:
        pass


def _write_store_file(path: str, data: Dict[str, Any]) -> None:
    """Atomic write. A crash midway through json.dump used to leave a
    truncated payment file behind; writing to a temp file and renaming means
    the real path always holds a complete document."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _load_store() -> Dict[str, Any]:
    path = _payments_path()
    if not os.path.exists(path):
        return _restore_from_durable(path, "file missing") or _empty_store()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("orders", {})
        data.setdefault("users", {})
        data.setdefault("processed", {})
        return data
    except (json.JSONDecodeError, OSError) as exc:
        # Returning an empty store here was a silent money-record wipe: the
        # next _save_store() would overwrite the damaged file with that
        # emptiness, destroying the only copy of who paid. Keep the bad file,
        # then recover the real one from Postgres.
        _quarantine(path)
        return _restore_from_durable(path, f"unreadable: {type(exc).__name__}") or _empty_store()


def _save_store(data: Dict[str, Any]) -> None:
    path = _payments_path()
    _write_store_file(path, data)
    # Mirror to Postgres so the file is a cache, not the only copy.
    d = _durable()
    if d is not None:
        try:
            d.mirror(data, source="save")
        except Exception:  # noqa: BLE001
            pass


def is_configured() -> bool:
    return bool(PAGUELOFACIL_CCLW)


def parse_webhook_body(raw: bytes) -> Optional[Dict[str, Any]]:
    """Parse PagueloFacil POST body — tolerates encoding quirks in large binInfo payloads."""
    if not raw:
        return None
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        for errors in ("strict", "replace"):
            try:
                text = raw.decode(encoding, errors=errors)
                obj = json.loads(text)
                if isinstance(obj, dict):
                    return obj
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
    text = raw.decode("utf-8", errors="replace")
    related = re.search(r'"relatedTx"\s*:\s*"([^"]+)"', text)
    cod = re.search(r'"codOper"\s*:\s*"([^"]+)"', text)
    if not related and not cod:
        return None
    payload: Dict[str, Any] = {}
    if cod:
        payload["codOper"] = cod.group(1)
    if related:
        payload["relatedTx"] = related.group(1)
    for key, pattern in (
        ("authStatus", r'"authStatus"\s*:\s*"([^"]+)"'),
        ("totalPay", r'"totalPay"\s*:\s*"([^"]+)"'),
        ("description", r'"description"\s*:\s*"([^"]+)"'),
        ("PARM_1", r'"PARM_1"\s*:\s*"([^"]+)"'),
        ("email", r'"email"\s*:\s*"([^"]+@[^"]+)"'),
        ("status", r'"status"\s*:\s*(\d+)'),
    ):
        match = re.search(pattern, text)
        if match:
            val: Any = match.group(1)
            if key == "status":
                val = int(val)
            payload[key] = val
    logging.info("PagueloFacil: salvaged payload from raw regex keys=%s", list(payload.keys()))
    return payload


def _is_payment_approved(payload: Dict[str, Any]) -> bool:
    status = payload.get("status")
    if status in (1, "1", True):
        return True
    if str(payload.get("Estado", "")).lower() == "aprobada":
        return True
    auth = str(payload.get("authStatus") or "").strip()
    if auth in ("00", "0", "000"):
        return True
    try:
        total = float(payload.get("totalPay") or payload.get("requestPayAmount") or 0)
        if total > 0 and auth == "00":
            return True
    except (TypeError, ValueError):
        pass
    msg = str(payload.get("messageSys") or "").lower()
    return "aprob" in msg


def parse_parm1(value: str) -> Optional[Tuple[str, str]]:
    """Return (platform, canonical_user_id) from PARM_1 or prefixed id."""
    val = str(value or "").strip()
    if not val:
        return None
    upper = val.upper()
    if upper.startswith("WA:"):
        phone = normalize_whatsapp_id(val[3:])
        return (PLATFORM_WHATSAPP, phone) if phone else None
    if upper.startswith("TG:"):
        tg = val[3:].strip()
        return (PLATFORM_TELEGRAM, tg) if tg.isdigit() else None
    if val.isdigit():
        # Backward compatible: bare numeric id = Telegram user id
        return PLATFORM_TELEGRAM, val
    return None


def store_keys_for_user(platform: str, user_id: str) -> List[str]:
    """All JSON store keys that may hold this user's access (lookup order)."""
    if platform == PLATFORM_WHATSAPP:
        wa = normalize_whatsapp_id(user_id)
        digits = "".join(c for c in wa if c.isdigit())
        keys = [f"wa:{wa}", f"wa:{digits}", wa, digits]
        return list(dict.fromkeys(k for k in keys if k))
    tg = str(user_id)
    return list(dict.fromkeys([tg, f"tg:{tg}"]))


def primary_store_key(platform: str, user_id: str) -> str:
    if platform == PLATFORM_WHATSAPP:
        return f"wa:{normalize_whatsapp_id(user_id)}"
    return str(user_id)


def _parse_platform_user_from_description(description: str) -> Optional[Tuple[str, str]]:
    wa_match = WA_USER_RE.search(description)
    if wa_match:
        phone = normalize_whatsapp_id(wa_match.group(1))
        if phone:
            return PLATFORM_WHATSAPP, phone
    tg_match = TG_USER_RE.search(description)
    if tg_match:
        return PLATFORM_TELEGRAM, tg_match.group(1)
    return None


def _extract_platform_user(payload: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    for key in ("PARM_1", "parm_1", "parm1"):
        val = payload.get(key)
        if val:
            parsed = parse_parm1(str(val))
            if parsed:
                return parsed

    description = str(payload.get("description") or payload.get("CDSC") or "")
    parsed = _parse_platform_user_from_description(description)
    if parsed:
        return parsed

    email = str(payload.get("email") or "").lower()
    if email:
        store = _load_store()
        for order in store.get("orders", {}).values():
            if order.get("email") == email:
                platform = order.get("platform") or PLATFORM_TELEGRAM
                uid = order.get("user_id") or order.get("telegram_id") or order.get("whatsapp_id")
                if uid:
                    return platform, str(uid)

    related = str(payload.get("relatedTx") or payload.get("codOper") or "")
    if related.startswith("LK-"):
        store = _load_store()
        for code, order in store.get("orders", {}).items():
            uid = order.get("user_id") or order.get("telegram_id") or order.get("whatsapp_id")
            platform = order.get("platform") or (
                PLATFORM_WHATSAPP if order.get("whatsapp_id") else PLATFORM_TELEGRAM
            )
            if uid and (
                code == related
                or related.startswith(code[:12])
                or code.startswith(related[:12])
            ):
                return platform, str(uid)
    return None


def _extract_telegram_id(payload: Dict[str, Any]) -> Optional[str]:
    """Backward-compatible helper — Telegram ids only."""
    parsed = _extract_platform_user(payload)
    if parsed and parsed[0] == PLATFORM_TELEGRAM:
        return parsed[1]
    return None


def _find_user_entry(user_id: str, platform: Optional[str] = None) -> Optional[Tuple[str, Dict[str, Any]]]:
    store = _load_store()
    platforms = [platform] if platform else [PLATFORM_TELEGRAM, PLATFORM_WHATSAPP]
    for plat in platforms:
        for key in store_keys_for_user(plat, user_id):
            entry = store.get("users", {}).get(key)
            if entry:
                return key, entry
    return None


def has_active_access(user_id: str, platform: Optional[str] = None) -> bool:
    found = _find_user_entry(user_id, platform)
    if not found:
        return False
    _, entry = found
    paid_until = entry.get("paid_until")
    if not paid_until:
        return False
    try:
        return datetime.now() < datetime.fromisoformat(paid_until)
    except ValueError:
        return False


def format_paid_until_display(paid_until_iso: Optional[str]) -> str:
    """Human-readable expiry for user-facing messages."""
    if not paid_until_iso:
        return "30 días / 30 days"
    try:
        dt = datetime.fromisoformat(paid_until_iso)
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return paid_until_iso[:10]


def get_access_info(user_id: str, platform: Optional[str] = None) -> Dict[str, Any]:
    found = _find_user_entry(user_id, platform)
    if not found or not has_active_access(user_id, platform):
        return {
            "active": False,
            "paid_until": None,
            "days_remaining": 0,
            "hours_remaining": 0,
        }
    _, entry = found
    paid_until = datetime.fromisoformat(entry["paid_until"])
    delta = paid_until - datetime.now()
    days = max(0, delta.days)
    hours = max(0, delta.total_seconds() / 3600)
    return {
        "active": True,
        "paid_until": entry["paid_until"],
        "paid_until_display": format_paid_until_display(entry["paid_until"]),
        "days_remaining": days,
        "hours_remaining": hours,
        "reminders_sent": list(entry.get("reminders_sent") or []),
        "last_cod_oper": entry.get("last_cod_oper"),
        "platform": entry.get("platform"),
    }


def mark_pf_reminder_sent(user_id: str, reminder_key: str, platform: Optional[str] = None) -> bool:
    """Record that a PF expiry reminder was sent. Returns True if newly recorded."""
    found = _find_user_entry(user_id, platform)
    if not found:
        return False
    store_key, entry = found
    sent = list(entry.get("reminders_sent") or [])
    if reminder_key in sent:
        return False
    sent.append(reminder_key)
    store = _load_store()
    store["users"][store_key]["reminders_sent"] = sent
    _save_store(store)
    return True


def grant_access(
    user_id: str,
    *,
    cod_oper: str,
    amount: Optional[str] = None,
    email: Optional[str] = None,
    days: Optional[int] = None,
    platform: str = PLATFORM_TELEGRAM,
) -> Dict[str, Any]:
    if platform == PLATFORM_WHATSAPP:
        user_id = normalize_whatsapp_id(user_id)
    else:
        user_id = str(user_id)

    access_days = days or PAGUELOFACIL_ACCESS_DAYS
    store = _load_store()
    now = datetime.now()
    store_key = primary_store_key(platform, user_id)

    existing = store["users"].get(store_key, {})
    base = now
    if existing.get("paid_until"):
        try:
            current_end = datetime.fromisoformat(existing["paid_until"])
            if current_end > now:
                base = current_end
        except ValueError:
            pass

    paid_until = (base + timedelta(days=access_days)).isoformat()
    entry: Dict[str, Any] = {
        "platform": platform,
        "user_id": user_id,
        "paid_until": paid_until,
        "last_cod_oper": cod_oper,
        "last_amount": amount,
        "email": email or existing.get("email"),
        "source": "paguelofacil",
        "updated_at": now.isoformat(),
        "reminders_sent": [],
    }
    if platform == PLATFORM_TELEGRAM:
        entry["telegram_id"] = user_id
    else:
        entry["whatsapp_id"] = user_id

    store["users"][store_key] = entry
    store["processed"][cod_oper] = {
        "platform": platform,
        "user_id": user_id,
        "paid_until": paid_until,
        "at": now.isoformat(),
    }
    _save_store(store)
    logging.info(
        "PagueloFacil: granted %s days to %s %s (codOper=%s)",
        access_days,
        platform,
        user_id,
        cod_oper,
    )
    return {
        "user_id": user_id,
        "platform": platform,
        "paid_until": paid_until,
        "days_added": access_days,
    }


def create_payment_link(user_id: str, platform: str = PLATFORM_TELEGRAM) -> Dict[str, Any]:
    """Request a secure checkout URL from PagueloFacil LinkDeamon."""
    if not is_configured():
        return {
            "success": False,
            "error": "PAGUELOFACIL_CCLW not configured — add merchant CCLW to .env on Oracle.",
        }

    amount = PAGUELOFACIL_AMOUNT_WA if platform == PLATFORM_WHATSAPP else PAGUELOFACIL_AMOUNT

    if platform == PLATFORM_WHATSAPP:
        wa_id = normalize_whatsapp_id(user_id)
        description = f"EspaLuz WhatsApp — WA:{wa_id} — 1 mes acceso"
        parm1 = f"WA:{wa_id.lstrip('+')}"
        canonical_id = wa_id
    else:
        tg_id = str(user_id)
        description = f"EspaLuz Telegram — TG:{tg_id} — 1 mes acceso"
        parm1 = tg_id
        canonical_id = tg_id

    data = {
        "CCLW": PAGUELOFACIL_CCLW,
        "CMTN": amount,
        "CDSC": description[:150],
        "PARM_1": parm1,
        "EXPIRES_IN": 3600,
    }

    try:
        response = requests.post(
            LINK_URL,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "*/*",
            },
            timeout=30,
            allow_redirects=True,
        )
        response.raise_for_status()
        body = response.json()
    except requests.RequestException as exc:
        logging.error("PagueloFacil link error: %s", exc)
        return {"success": False, "error": f"PagueloFacil request failed: {exc}"}
    except json.JSONDecodeError:
        return {"success": False, "error": "PagueloFacil returned non-JSON response"}

    if not body.get("success"):
        return {"success": False, "error": body.get("message") or "PagueloFacil rejected link request"}

    checkout = body.get("data") or {}
    url = checkout.get("url")
    code = checkout.get("code")
    if not url:
        return {"success": False, "error": "No checkout URL in PagueloFacil response"}

    store = _load_store()
    if code:
        order: Dict[str, Any] = {
            "platform": platform,
            "user_id": canonical_id,
            "amount": amount,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "sandbox": PAGUELOFACIL_SANDBOX,
        }
        if platform == PLATFORM_TELEGRAM:
            order["telegram_id"] = canonical_id
        else:
            order["whatsapp_id"] = canonical_id
        store["orders"][code] = order
        _save_store(store)

    return {"success": True, "url": url, "code": code, "amount": amount, "platform": platform}


def notify_whatsapp_user_paid(whatsapp_id: str, paid_until: Optional[str] = None) -> bool:
    if not PAGUELOFACIL_WA_NOTIFY_URL:
        logging.warning("PagueloFacil: WA notify URL not configured")
        return False
    wa_id = normalize_whatsapp_id(whatsapp_id)
    payload = {
        "whatsapp_id": wa_id,
        "paid_until": paid_until,
    }
    headers = {"Content-Type": "application/json"}
    if INTERNAL_WEBHOOK_SECRET:
        headers["Authorization"] = f"Bearer {INTERNAL_WEBHOOK_SECRET}"
    try:
        resp = requests.post(PAGUELOFACIL_WA_NOTIFY_URL, json=payload, headers=headers, timeout=15)
        if resp.status_code == 200:
            return True
        logging.warning("PagueloFacil: WA notify HTTP %s: %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logging.warning("PagueloFacil: WA notify failed for %s: %s", wa_id, exc)
    return False


def notify_user_paid(
    user_id: str,
    cod_oper: str,
    paid_until: Optional[str] = None,
    platform: str = PLATFORM_TELEGRAM,
) -> bool:
    if platform == PLATFORM_WHATSAPP:
        return notify_whatsapp_user_paid(user_id, paid_until)

    if not TELEGRAM_BOT_TOKEN:
        return False
    text = (
        "✅ ¡Pago recibido! / Payment received!\n\n"
        f"Tu acceso a EspaLuz está activo hasta {format_paid_until_display(paid_until)}.\n"
        "Your EspaLuz access is now active.\n\n"
        "¡Sigue practicando! Send me a message to continue. 🚀"
    )
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": int(user_id), "text": text},
            timeout=15,
        )
        return resp.status_code == 200
    except Exception as exc:
        logging.warning("PagueloFacil: Telegram notify failed for %s: %s", user_id, exc)
        return False


def process_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle PagueloFacil POST notification — idempotent."""
    cod_oper = str(payload.get("codOper") or payload.get("relatedTx") or "")
    if not cod_oper:
        return {"processed": False, "reason": "missing_codOper"}

    store = _load_store()
    if cod_oper in store.get("processed", {}):
        return {"processed": True, "reason": "duplicate", "cod_oper": cod_oper}

    approved = _is_payment_approved(payload)
    op_type = str(payload.get("operationType") or payload.get("merchantDescriptor") or "")
    if op_type and op_type not in ("AUTH_CAPTURE", "CAPTURE", "RECURRENT", "PF*", ""):
        logging.info("PagueloFacil: note operationType=%s codOper=%s", op_type, cod_oper)

    if not approved:
        return {
            "processed": False,
            "reason": "not_approved",
            "cod_oper": cod_oper,
            "status": payload.get("status"),
            "authStatus": payload.get("authStatus"),
        }

    parsed = _extract_platform_user(payload)
    if not parsed:
        logging.warning("PagueloFacil: approved but no user id in payload codOper=%s", cod_oper)
        return {"processed": False, "reason": "no_user_id", "cod_oper": cod_oper}

    platform, user_id = parsed
    amount = str(payload.get("totalPay") or payload.get("requestPayAmount") or PAGUELOFACIL_AMOUNT)
    email = payload.get("email")
    result = grant_access(
        user_id,
        cod_oper=cod_oper,
        amount=amount,
        email=email,
        platform=platform,
    )
    notify_ok = notify_user_paid(user_id, cod_oper, result.get("paid_until"), platform=platform)
    return {"processed": True, "cod_oper": cod_oper, "notify_ok": notify_ok, **result}


paguelofacil_system = type("PagueloFacilSystem", (), {
    "is_configured": staticmethod(is_configured),
    "parse_webhook_body": staticmethod(parse_webhook_body),
    "create_payment_link": staticmethod(create_payment_link),
    "process_webhook": staticmethod(process_webhook),
    "has_active_access": staticmethod(has_active_access),
    "get_access_info": staticmethod(get_access_info),
    "grant_access": staticmethod(grant_access),
    "notify_user_paid": staticmethod(notify_user_paid),
    "notify_whatsapp_user_paid": staticmethod(notify_whatsapp_user_paid),
    "PLATFORM_TELEGRAM": PLATFORM_TELEGRAM,
    "PLATFORM_WHATSAPP": PLATFORM_WHATSAPP,
})()
