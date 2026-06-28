#!/usr/bin/env python3
"""
EspaLuz PagueloFacil — one-time monthly payments (no subscriptions).

Docs: https://developers.paguelofacil.com/guias/enlace-de-pago
Webhook: https://webhook.aideazz.xyz/paguelofacil-webhook (paypal_webhook_server.py)
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

PAGUELOFACIL_CCLW = os.getenv("PAGUELOFACIL_CCLW", "").strip()
PAGUELOFACIL_SANDBOX = os.getenv("PAGUELOFACIL_SANDBOX", "true").lower() in ("1", "true", "yes")
PAGUELOFACIL_AMOUNT = os.getenv("PAGUELOFACIL_AMOUNT", "11.00").strip()
PAGUELOFACIL_ACCESS_DAYS = int(os.getenv("PAGUELOFACIL_ACCESS_DAYS", "30"))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

LINK_URL = (
    "https://sandbox.paguelofacil.com/LinkDeamon.cfm"
    if PAGUELOFACIL_SANDBOX
    else "https://secure.paguelofacil.com/LinkDeamon.cfm"
)

PAYMENTS_FILE = "paguelofacil_payments.json"
TG_USER_RE = re.compile(r"(?:TG[:\s-]|user[:\s-])(\d{5,20})", re.I)


def _base_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _payments_path() -> str:
    return os.path.join(_base_dir(), PAYMENTS_FILE)


def _load_store() -> Dict[str, Any]:
    path = _payments_path()
    if not os.path.exists(path):
        return {"orders": {}, "users": {}, "processed": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("orders", {})
        data.setdefault("users", {})
        data.setdefault("processed", {})
        return data
    except (json.JSONDecodeError, OSError):
        return {"orders": {}, "users": {}, "processed": {}}


def _save_store(data: Dict[str, Any]) -> None:
    with open(_payments_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def is_configured() -> bool:
    return bool(PAGUELOFACIL_CCLW)


def _extract_telegram_id(payload: Dict[str, Any]) -> Optional[str]:
    for key in ("PARM_1", "parm_1", "parm1"):
        val = payload.get(key)
        if val and str(val).isdigit():
            return str(val)

    description = str(payload.get("description") or payload.get("CDSC") or "")
    match = TG_USER_RE.search(description)
    if match:
        return match.group(1)

    email = str(payload.get("email") or "").lower()
    if email:
        store = _load_store()
        for order in store.get("orders", {}).values():
            if order.get("email") == email and order.get("telegram_id"):
                return str(order["telegram_id"])
    return None


def has_active_access(user_id: str) -> bool:
    user_id = str(user_id)
    store = _load_store()
    entry = store.get("users", {}).get(user_id)
    if not entry:
        return False
    paid_until = entry.get("paid_until")
    if not paid_until:
        return False
    try:
        return datetime.now() < datetime.fromisoformat(paid_until)
    except ValueError:
        return False


def get_access_info(user_id: str) -> Dict[str, Any]:
    user_id = str(user_id)
    if not has_active_access(user_id):
        return {"active": False, "paid_until": None, "days_remaining": 0}
    entry = _load_store().get("users", {}).get(user_id, {})
    paid_until = datetime.fromisoformat(entry["paid_until"])
    days = max(0, (paid_until - datetime.now()).days)
    return {
        "active": True,
        "paid_until": entry["paid_until"],
        "days_remaining": days,
        "last_cod_oper": entry.get("last_cod_oper"),
    }


def grant_access(
    user_id: str,
    *,
    cod_oper: str,
    amount: Optional[str] = None,
    email: Optional[str] = None,
    days: Optional[int] = None,
) -> Dict[str, Any]:
    user_id = str(user_id)
    access_days = days or PAGUELOFACIL_ACCESS_DAYS
    store = _load_store()
    now = datetime.now()

    existing = store["users"].get(user_id, {})
    base = now
    if existing.get("paid_until"):
        try:
            current_end = datetime.fromisoformat(existing["paid_until"])
            if current_end > now:
                base = current_end
        except ValueError:
            pass

    paid_until = (base + timedelta(days=access_days)).isoformat()
    store["users"][user_id] = {
        "telegram_id": user_id,
        "paid_until": paid_until,
        "last_cod_oper": cod_oper,
        "last_amount": amount,
        "email": email or existing.get("email"),
        "source": "paguelofacil",
        "updated_at": now.isoformat(),
    }
    store["processed"][cod_oper] = {
        "telegram_id": user_id,
        "paid_until": paid_until,
        "at": now.isoformat(),
    }
    _save_store(store)
    logging.info("PagueloFacil: granted %s days to TG %s (codOper=%s)", access_days, user_id, cod_oper)
    return {"user_id": user_id, "paid_until": paid_until, "days_added": access_days}


def create_payment_link(user_id: str) -> Dict[str, Any]:
    """Request a secure checkout URL from PagueloFacil LinkDeamon."""
    user_id = str(user_id)
    if not is_configured():
        return {
            "success": False,
            "error": "PAGUELOFACIL_CCLW not configured — add merchant CCLW to .env on Oracle.",
        }

    description = f"EspaLuz Telegram — TG:{user_id} — 1 mes acceso"
    data = {
        "CCLW": PAGUELOFACIL_CCLW,
        "CMTN": PAGUELOFACIL_AMOUNT,
        "CDSC": description[:150],
        "PARM_1": user_id,
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
        store["orders"][code] = {
            "telegram_id": user_id,
            "amount": PAGUELOFACIL_AMOUNT,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "sandbox": PAGUELOFACIL_SANDBOX,
        }
        _save_store(store)

    return {"success": True, "url": url, "code": code, "amount": PAGUELOFACIL_AMOUNT}


def process_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle PagueloFacil POST notification — idempotent."""
    cod_oper = str(payload.get("codOper") or payload.get("relatedTx") or "")
    if not cod_oper:
        return {"processed": False, "reason": "missing_codOper"}

    store = _load_store()
    if cod_oper in store.get("processed", {}):
        return {"processed": True, "reason": "duplicate", "cod_oper": cod_oper}

    status = payload.get("status")
    approved = status == 1 or status == "1" or str(payload.get("Estado", "")).lower() == "aprobada"
    op_type = str(payload.get("operationType") or payload.get("merchantDescriptor") or "")
    if op_type and op_type not in ("AUTH_CAPTURE", "CAPTURE", "RECURRENT", ""):
        logging.info("PagueloFacil: ignoring operationType=%s codOper=%s", op_type, cod_oper)

    if not approved:
        return {"processed": False, "reason": "not_approved", "cod_oper": cod_oper, "status": status}

    telegram_id = _extract_telegram_id(payload)
    if not telegram_id:
        logging.warning("PagueloFacil: approved but no telegram_id in payload codOper=%s", cod_oper)
        return {"processed": False, "reason": "no_telegram_id", "cod_oper": cod_oper}

    amount = str(payload.get("totalPay") or payload.get("requestPayAmount") or PAGUELOFACIL_AMOUNT)
    email = payload.get("email")
    result = grant_access(telegram_id, cod_oper=cod_oper, amount=amount, email=email)
    notify_user_paid(telegram_id, cod_oper, result.get("paid_until"))
    return {"processed": True, "cod_oper": cod_oper, **result}


def notify_user_paid(user_id: str, cod_oper: str, paid_until: Optional[str] = None) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        return False
    text = (
        "✅ ¡Pago recibido! / Payment received!\n\n"
        f"Tu acceso a EspaLuz está activo hasta {paid_until or '30 días'}.\n"
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


paguelofacil_system = type("PagueloFacilSystem", (), {
    "is_configured": staticmethod(is_configured),
    "create_payment_link": staticmethod(create_payment_link),
    "process_webhook": staticmethod(process_webhook),
    "has_active_access": staticmethod(has_active_access),
    "get_access_info": staticmethod(get_access_info),
    "grant_access": staticmethod(grant_access),
    "notify_user_paid": staticmethod(notify_user_paid),
})()
