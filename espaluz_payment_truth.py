"""EspaLuz payment truth (1 Nov 2026, docs/espaluz/ONE_PAYMENT_TRUTH_PLAN_2026-11-01.md in cto-aipa).

Elena: "single source of truth, reliable detection, nothing lost and nothing duplicated." Who has paid, and until when,
lives in ONE place: `espaluz_unified.subscribers` - the table the WhatsApp gate already reads (user_trial_system.py),
keyed by email with both channel ids. This module only adds what was missing:

- `paid_until` on that table: PayPal = the next billing date PayPal itself reports (+3 days grace), so PayPal's own free
  weeks are honoured exactly; PágueloFácil = 30 days per payment, stacked. A cancel never takes back a paid month.
- `payment_events`: every payment counted ONCE, keyed (provider, event_id). The same webhook delivered 1 or 10 times
  moves `paid_until` once - idempotency.
- PayPal events count only after PayPal confirms their signature (each PayPal app has its own webhook id).
- `reconcile()`: re-reads every known PayPal subscription from PayPal, so a missed or dropped webhook can never leave a
  paying family "expired" (the 26 Oct $7.77 renewal reached the WhatsApp bot and was dropped for having no email).

Used by the three doors that already exist: paypal_webhook_server.py (Telegram PayPal app + PágueloFácil) and the
WhatsApp bridge's /paypal-webhook (WhatsApp PayPal app).
"""
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone

import psycopg2
import requests

PAYPAL_API = "https://api-m.paypal.com"
GRACE = timedelta(days=3)  # PayPal retries a failed charge for a few days before it suspends
MONTH = timedelta(days=31)
_BASE = os.path.dirname(os.path.abspath(__file__))


def _db_url():
    return os.getenv("ESPALUZ_UNIFIED_DB_URL") or os.getenv("DATABASE_URL_UNIFIED")


def _conn():
    return psycopg2.connect(_db_url())


def ensure_schema():
    with _conn() as c, c.cursor() as cur:
        cur.execute("ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS paid_until TIMESTAMPTZ")
        cur.execute("""CREATE TABLE IF NOT EXISTS payment_events (
                         provider TEXT NOT NULL, event_id TEXT NOT NULL, kind TEXT, payer TEXT, amount TEXT,
                         received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (provider, event_id))""")


def first_time(provider, event_id, kind=None, payer=None, amount=None):
    """True only the first time this payment event is seen (the idempotency key)."""
    with _conn() as c, c.cursor() as cur:
        cur.execute("INSERT INTO payment_events (provider, event_id, kind, payer, amount) VALUES (%s,%s,%s,%s,%s) "
                    "ON CONFLICT (provider, event_id) DO NOTHING", (provider, str(event_id), kind, payer, amount))
        return cur.rowcount == 1


def _record(key, status, source, paid_until=None, sub_data=None, telegram_id=None, whatsapp_id=None):
    """Upsert one family's row. paid_until only ever grows. One email can hold several PayPal subscriptions (Elena's
    family holds 12, measured 1 Nov): every id is kept in `paypal_subscription_ids` for the safety net, and one
    subscription that stopped never marks the family inactive while its paid time still runs."""
    sub_data = dict(sub_data or {})
    sid = sub_data.get("paypal_subscription_id")
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            """INSERT INTO subscribers (email, telegram_id, whatsapp_id, status, source, last_updated, subscription_data, paid_until)
               VALUES (%s,%s,%s,%s,%s,NOW(),%s::jsonb || jsonb_build_object('paypal_subscription_ids',
                       CASE WHEN %s::text IS NULL THEN '[]'::jsonb ELSE jsonb_build_array(%s::text) END),%s)
               ON CONFLICT (email) DO UPDATE SET
                 telegram_id = COALESCE(EXCLUDED.telegram_id, subscribers.telegram_id),
                 whatsapp_id = COALESCE(EXCLUDED.whatsapp_id, subscribers.whatsapp_id),
                 status = CASE WHEN EXCLUDED.status = 'active' THEN 'active'
                               WHEN subscribers.status = 'active' AND subscribers.paid_until > NOW() THEN 'active'
                               ELSE EXCLUDED.status END,
                 source = EXCLUDED.source, last_updated = NOW(),
                 subscription_data = COALESCE(subscribers.subscription_data, '{}'::jsonb) || EXCLUDED.subscription_data
                   || jsonb_build_object('paypal_subscription_ids', (
                        SELECT COALESCE(jsonb_agg(DISTINCT v), '[]'::jsonb) FROM jsonb_array_elements_text(
                          COALESCE(subscribers.subscription_data->'paypal_subscription_ids', '[]'::jsonb)
                          || COALESCE(EXCLUDED.subscription_data->'paypal_subscription_ids', '[]'::jsonb)) v)),
                 paid_until = GREATEST(subscribers.paid_until, EXCLUDED.paid_until)""",
            (key.lower(), telegram_id, whatsapp_id, status, source, json.dumps(sub_data), sid, sid, paid_until))


def access(emails=(), telegram_id=None, whatsapp_id=None):
    """What the gates ask (plan phase 2): this person's row that is paid the longest, found by any of their ids
    (email, Telegram id, or the phone WhatsApp linking stored in telegram_id/whatsapp_id). None = no row, or the
    database could not answer - then the caller keeps its old checks rather than locking anyone out."""
    digits = re.sub(r"\D", "", str(whatsapp_id or "")) or None
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute(
                """SELECT email, status, source, paid_until, paid_until > NOW() FROM subscribers
                   WHERE lower(email) = ANY(%s) OR telegram_id = %s
                      OR (%s::text IS NOT NULL AND (regexp_replace(coalesce(whatsapp_id,''), '\\D', '', 'g') = %s
                                                    OR regexp_replace(coalesce(telegram_id,''), '\\D', '', 'g') = %s))
                   ORDER BY paid_until DESC NULLS LAST LIMIT 1""",
                ([e.lower() for e in emails if e], str(telegram_id) if telegram_id else None, digits, digits, digits))
            row = cur.fetchone()
    except Exception as e:
        logging.warning(f"payment truth: access lookup failed: {e}")
        return None
    if not row:
        return None
    return {"email": row[0], "status": row[1], "source": row[2], "paid_until": row[3], "paid": bool(row[4])}


# ---------------- PayPal ----------------

def _token(client_id, secret):
    r = requests.post(PAYPAL_API + "/v1/oauth2/token", auth=(client_id, secret),
                      data={"grant_type": "client_credentials"}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def paypal_verified(headers, event, client_id, secret, webhook_id):
    """PayPal's own check that this webhook really came from PayPal for this app."""
    if not (client_id and secret and webhook_id):
        return False
    try:
        h = {k.lower(): v for k, v in headers.items()}
        body = {"auth_algo": h.get("paypal-auth-algo"), "cert_url": h.get("paypal-cert-url"),
                "transmission_id": h.get("paypal-transmission-id"), "transmission_sig": h.get("paypal-transmission-sig"),
                "transmission_time": h.get("paypal-transmission-time"), "webhook_id": webhook_id, "webhook_event": event}
        r = requests.post(PAYPAL_API + "/v1/notifications/verify-webhook-signature", json=body, timeout=30,
                          headers={"Authorization": "Bearer " + _token(client_id, secret)})
        return r.status_code == 200 and r.json().get("verification_status") == "SUCCESS"
    except Exception as e:
        logging.warning(f"payment truth: PayPal verify failed: {e}")
        return False


def _iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def paypal_sync(subscription_id, client_id, secret):
    """Read one subscription from PayPal and write the truth: status, email, plan, paid_until."""
    r = requests.get(f"{PAYPAL_API}/v1/billing/subscriptions/{subscription_id}", timeout=30,
                     headers={"Authorization": "Bearer " + _token(client_id, secret)})
    if r.status_code != 200:
        logging.warning(f"payment truth: PayPal {subscription_id[:6]}… HTTP {r.status_code}")
        return None
    s = r.json()
    email = (s.get("subscriber") or {}).get("email_address")
    if not email:
        return None
    info = s.get("billing_info") or {}
    status = {"ACTIVE": "active", "SUSPENDED": "suspended", "CANCELLED": "cancelled", "EXPIRED": "expired",
              "APPROVAL_PENDING": "pending", "APPROVED": "pending"}.get(s.get("status"), (s.get("status") or "").lower())
    nxt = _iso(info.get("next_billing_time"))
    last = _iso((info.get("last_payment") or {}).get("time"))
    if status == "active" and nxt:
        paid_until = nxt + GRACE  # includes PayPal's own free weeks: the first charge date is the next billing time
    elif last:
        paid_until = last + MONTH  # cancelled/suspended: the month already paid still runs
    else:
        paid_until = None
    _record(email, status, "paypal", paid_until,
            {"paypal_subscription_id": subscription_id, "paypal_plan_id": s.get("plan_id")})
    logging.warning(f"💳 payment truth: PayPal {s.get('plan_id', '')[:8]}… {status} paid_until "
                    f"{paid_until.date() if paid_until else None}")
    return {"status": status, "paid_until": paid_until}


def paypal_event(headers, event, client_id, secret, webhook_id):
    """One PayPal webhook through the one door: verify, count once, then read the truth from PayPal."""
    if not paypal_verified(headers, event, client_id, secret, webhook_id):
        logging.warning(f"💳 payment truth: PayPal event NOT verified ({event.get('event_type')}) - ignored")
        return "unverified"
    res = event.get("resource") or {}
    kind = event.get("event_type", "")
    sub_id = res.get("billing_agreement_id") if kind.startswith("PAYMENT.") else res.get("id")
    if not first_time("paypal", event.get("id"), kind, sub_id, (res.get("amount") or {}).get("total")):
        return "duplicate"
    if sub_id and str(sub_id).startswith("I-"):
        paypal_sync(sub_id, client_id, secret)
    return "recorded"


# ---------------- PágueloFácil ----------------

def pf_payment(platform, user_id, cod_oper, amount, email, paid_until_iso):
    """After the existing grant_access: the same payment, counted once, in the truth table."""
    if not first_time("paguelofacil", cod_oper, "paid", f"{platform}:{user_id}", amount):
        return "duplicate"
    paid_until = datetime.fromisoformat(paid_until_iso)
    if paid_until.tzinfo is None:
        paid_until = paid_until.astimezone(timezone.utc)
    key = email or f"{platform}:{user_id}"  # a payer without email is keyed by the channel id that paid
    _record(key, "active", "paguelofacil", paid_until, {"last_cod_oper": cod_oper},
            telegram_id=user_id if platform == "telegram" else None,
            whatsapp_id=user_id if platform == "whatsapp" else None)
    logging.warning(f"💳 payment truth: PágueloFácil {platform} paid_until {paid_until.date()}")
    return "recorded"


# ---------------- Safety net ----------------

def _known_subscription_ids():
    ids = set()
    with _conn() as c, c.cursor() as cur:
        cur.execute("SELECT jsonb_array_elements_text(subscription_data->'paypal_subscription_ids') FROM subscribers "
                    "WHERE jsonb_typeof(subscription_data->'paypal_subscription_ids') = 'array' "
                    "UNION SELECT subscription_data->>'paypal_subscription_id' FROM subscribers")
        ids |= {r[0] for r in cur.fetchall() if r[0]}
    wa = os.getenv("ESPALUZ_WHATSAPP_DIR", os.path.join(os.path.dirname(_BASE), "EspaLuzWhatsApp"))
    for path in (os.path.join(_BASE, "telegram_subscribers.json"), os.path.join(_BASE, "discovered_subscription_ids.json"),
                 os.path.join(wa, "subscribers.json")):
        try:
            text = open(path, encoding="utf-8").read()
        except OSError:
            continue
        ids |= set(re.findall(r"\bI-[A-Z0-9]{10,}\b", text))
    return ids


def _recent_paypal_subscription_ids(client_id, secret, days=31):
    """Every subscription PayPal charged in the last month - so a new payer is found even if no webhook reached us
    (the Telegram app's webhook is not subscribed to monthly payments)."""
    end = datetime.now(timezone.utc)
    r = requests.get(PAYPAL_API + "/v1/reporting/transactions", timeout=60,
                     headers={"Authorization": "Bearer " + _token(client_id, secret)},
                     params={"start_date": (end - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                             "end_date": end.strftime("%Y-%m-%dT%H:%M:%SZ"), "fields": "transaction_info", "page_size": 500})
    if r.status_code != 200:
        return set()
    return {t["transaction_info"]["paypal_reference_id"] for t in r.json().get("transaction_details", [])
            if t["transaction_info"].get("paypal_reference_id_type") in ("RP", "SUB")
            and str(t["transaction_info"].get("paypal_reference_id", "")).startswith("I-")}


def reconcile(client_id, secret):
    """Re-read every known PayPal subscription from PayPal (both EspaLuz apps share one merchant account)."""
    done = 0
    try:
        recent = _recent_paypal_subscription_ids(client_id, secret)
    except Exception as e:
        logging.warning(f"payment truth: transaction search failed: {e}")
        recent = set()
    for sub_id in sorted(_known_subscription_ids() | recent):
        try:
            if paypal_sync(sub_id, client_id, secret):
                done += 1
        except Exception as e:
            logging.warning(f"payment truth: reconcile {sub_id[:6]}…: {e}")
    logging.warning(f"💳 payment truth: reconcile synced {done} PayPal subscription(s)")
    return done
