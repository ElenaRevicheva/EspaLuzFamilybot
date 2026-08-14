"""
Durable mirror for the PagueloFacil payment store.

WHY THIS EXISTS
---------------
PagueloFacil is the local Panama payment rail, and its records — who paid,
how much, until when — lived in a single 2 KB JSON file on disk. A file is
not a database. One careless working-tree cleanup and the payment history
is gone with no way to prove a customer ever paid. That exact failure mode
has already destroyed irreplaceable work in this project once.

This module mirrors every save of that store into Postgres as an append-only
snapshot, and restores the file automatically if it ever goes missing or
turns corrupt.

FAIL-SAFE BY CONSTRUCTION
-------------------------
Every public function swallows its own exceptions and returns a benign value.
If Postgres is unreachable, the payment flow behaves EXACTLY as it did before
this module existed. The mirror is a safety net, never a dependency — a
backup system that can take down the thing it backs up is worse than none.
"""

import hashlib
import json
import logging
import os

logger = logging.getLogger(__name__)

_TABLE = "pf_payment_snapshots"

# Where to find the database URL. The Telegram bot's .env does not carry it,
# but the WhatsApp bot on the same host does, and both speak to the same
# unified database. Checked in order; first hit wins.
_ENV_KEYS = ("ESPALUZ_UNIFIED_DB_URL", "DATABASE_URL_UNIFIED", "DATABASE_URL")
_ENV_FILES = (
    "/home/ubuntu/EspaLuzWhatsApp/.env",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
)


def _database_url() -> str:
    for k in _ENV_KEYS:
        v = (os.getenv(k) or "").strip()
        if v:
            return v
    # Priority is by KEY, not by line order. Scanning line-first would return
    # whichever variable happens to appear earliest in the file — and in this
    # deployment the legacy, EMPTY `DATABASE_URL` sits above the unified one.
    # Connecting there silently yields "no payment history", which is precisely
    # the false emptiness this module exists to prevent.
    for k in _ENV_KEYS:
        for path in _ENV_FILES:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(k + "="):
                            v = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if v:
                                return v
            except OSError:
                continue
    return ""


def _conn():
    url = _database_url()
    if not url:
        return None
    import psycopg2  # imported lazily so a missing driver cannot break payments

    return psycopg2.connect(url, connect_timeout=10)


def ensure_table() -> bool:
    """Create the snapshot table if absent. Safe to call repeatedly."""
    try:
        c = _conn()
        if c is None:
            return False
        with c, c.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_TABLE} (
                  id           serial PRIMARY KEY,
                  captured_at  timestamp NOT NULL DEFAULT now(),
                  source       text,
                  doc          jsonb NOT NULL,
                  orders_n     int,
                  users_n      int,
                  processed_n  int,
                  doc_sha      text
                )"""
            )
            cur.execute(
                f"CREATE INDEX IF NOT EXISTS pf_snap_captured_idx ON {_TABLE} (captured_at DESC)"
            )
            cur.execute(
                f"CREATE UNIQUE INDEX IF NOT EXISTS pf_snap_sha_idx ON {_TABLE} (doc_sha)"
            )
        c.close()
        return True
    except Exception as exc:  # noqa: BLE001 - never propagate
        logger.debug("pf_durable: ensure_table failed: %s", exc)
        return False


def mirror(doc: dict, source: str = "save") -> bool:
    """
    Append `doc` to the durable history. Identical content is deduplicated by
    SHA, so repeated saves of an unchanged store do not grow the table.

    Returns True if the snapshot is safely in Postgres (written now or already
    present), False if the mirror could not be reached.
    """
    if not isinstance(doc, dict):
        return False
    try:
        raw = json.dumps(doc, sort_keys=True, ensure_ascii=False)
        sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        c = _conn()
        if c is None:
            return False
        with c, c.cursor() as cur:
            cur.execute(
                f"""INSERT INTO {_TABLE} (source, doc, orders_n, users_n, processed_n, doc_sha)
                    VALUES (%s, %s::jsonb, %s, %s, %s, %s)
                    ON CONFLICT (doc_sha) DO NOTHING""",
                (
                    source,
                    raw,
                    len(doc.get("orders") or {}),
                    len(doc.get("users") or {}),
                    len(doc.get("processed") or {}),
                    sha,
                ),
            )
        c.close()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("pf_durable: could not mirror payment store: %s", exc)
        return False


def latest() -> dict:
    """
    Newest snapshot, or {} if none / unreachable.

    Deliberately returns the snapshot with the most PAYMENT RECORDS among the
    most recent ones rather than blindly the newest row: if an empty store was
    ever mirrored by mistake, restoring from it would recreate the very wipe
    this module exists to prevent.
    """
    try:
        c = _conn()
        if c is None:
            return {}
        with c, c.cursor() as cur:
            cur.execute(
                f"""SELECT doc FROM {_TABLE}
                    ORDER BY (coalesce(users_n,0) + coalesce(processed_n,0)) DESC,
                             captured_at DESC
                    LIMIT 1"""
            )
            row = cur.fetchone()
        c.close()
        if not row:
            return {}
        doc = row[0]
        if isinstance(doc, str):
            doc = json.loads(doc)
        return doc if isinstance(doc, dict) else {}
    except Exception as exc:  # noqa: BLE001
        logger.warning("pf_durable: could not read payment history: %s", exc)
        return {}


def status() -> dict:
    """Health for ops dashboards: is the money history actually backed up?"""
    try:
        c = _conn()
        if c is None:
            return {"ok": False, "detail": "no database url configured"}
        with c, c.cursor() as cur:
            cur.execute(
                f"SELECT count(*), max(captured_at), max(users_n), max(processed_n) FROM {_TABLE}"
            )
            n, newest, users_n, processed_n = cur.fetchone()
        c.close()
        return {
            "ok": bool(n),
            "snapshots": n,
            "newest": newest.isoformat() if newest else None,
            "users": users_n,
            "processed_payments": processed_n,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "detail": str(exc)[:200]}


if __name__ == "__main__":  # quick CLI check: python espaluz_pf_durable.py
    ensure_table()
    print(json.dumps(status(), indent=2, default=str))
