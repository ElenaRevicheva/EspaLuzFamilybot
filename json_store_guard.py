"""
No-wipe guard for every EspaLuz JSON data store.

WHY
---
Both EspaLuz bots keep real state in JSON files on disk: Telegram trials,
subscribers, sessions, onboarding, phone/email mappings. Files are not a
database. A cleanup, a bad deploy, or a truncated write and that state is
gone — and in this project that has already happened once, permanently.

WHAT IT DOES
------------
Walks a fixed list of data files and appends each one to Postgres as an
append-only, SHA-deduplicated snapshot. Unchanged files cost nothing. Any
file can be restored later, from any point in its history.

WHY A TIMER AND NOT A CODE CHANGE
---------------------------------
Nothing here imports bot code and no bot code imports this. The bots cannot
be broken by a backup system they are not aware of. That is the entire point:
protection bought at zero risk to the features Elena depends on.

SECRETS ARE NEVER SNAPSHOTTED — see _DENY.

CLI
---
  python json_store_guard.py snapshot          # capture everything now
  python json_store_guard.py status            # what is protected, how fresh
  python json_store_guard.py history <file>    # snapshots for one file
  python json_store_guard.py restore <file>    # rewrite newest snapshot to disk
"""

import hashlib
import json
import os
import sys
from datetime import datetime

_TABLE = "json_store_snapshots"

APPS = {
    "familybot": "/home/ubuntu/EspaLuzFamilybot",
    "whatsapp": "/home/ubuntu/EspaLuzWhatsApp",
}

# Credentials and tokens must never land in a snapshot table. Anything whose
# name suggests a secret is skipped even if it is valid JSON.
_DENY = ("credential", "token", "secret", "key.json", "service_account")

_ENV_KEYS = ("ESPALUZ_UNIFIED_DB_URL", "DATABASE_URL_UNIFIED", "DATABASE_URL")
_ENV_FILES = (
    "/home/ubuntu/EspaLuzWhatsApp/.env",
    "/home/ubuntu/EspaLuzFamilybot/.env",
)

# Files large enough to be conversation logs rather than state are still worth
# keeping, but a cap stops one runaway file from bloating the table.
_MAX_BYTES = 8 * 1024 * 1024


def _database_url() -> str:
    # Priority by KEY, not by line order: the legacy `DATABASE_URL` in these
    # .env files points at an EMPTY database and appears above the unified one.
    for k in _ENV_KEYS:
        v = (os.getenv(k) or "").strip()
        if v:
            return v
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
    import psycopg2

    url = _database_url()
    if not url:
        raise RuntimeError("no database url found")
    return psycopg2.connect(url, connect_timeout=10)


def ensure_table() -> None:
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {_TABLE} (
              id          serial PRIMARY KEY,
              captured_at timestamp NOT NULL DEFAULT now(),
              app         text NOT NULL,
              rel_path    text NOT NULL,
              doc         jsonb NOT NULL,
              bytes       int,
              sha         text NOT NULL
            )"""
        )
        cur.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS jsg_path_sha_idx ON {_TABLE} (rel_path, sha)"
        )
        cur.execute(
            f"CREATE INDEX IF NOT EXISTS jsg_path_time_idx ON {_TABLE} (rel_path, captured_at DESC)"
        )


def _is_denied(name: str) -> bool:
    low = name.lower()
    return any(d in low for d in _DENY)


def _iter_files():
    """Every JSON data file in both bot directories, one level deep plus the
    known memory subfolder. Secrets excluded."""
    for app, root in APPS.items():
        if not os.path.isdir(root):
            continue
        candidates = []
        try:
            candidates += [f for f in os.listdir(root) if f.endswith(".json")]
        except OSError:
            pass
        sub = os.path.join(root, "family_memory_data")
        if os.path.isdir(sub):
            try:
                candidates += [
                    os.path.join("family_memory_data", f)
                    for f in os.listdir(sub)
                    if f.endswith(".json")
                ]
            except OSError:
                pass
        for rel in sorted(candidates):
            if _is_denied(rel):
                continue
            full = os.path.join(root, rel)
            if os.path.isfile(full):
                yield app, rel, full


def snapshot(verbose: bool = True) -> dict:
    """Capture all protected files. Returns a summary dict."""
    ensure_table()
    saved, unchanged, skipped = 0, 0, []
    with _conn() as c, c.cursor() as cur:
        for app, rel, full in _iter_files():
            try:
                size = os.path.getsize(full)
                if size > _MAX_BYTES:
                    skipped.append(f"{app}/{rel} (too large: {size} bytes)")
                    continue
                with open(full, "r", encoding="utf-8") as f:
                    doc = json.load(f)
            except (OSError, json.JSONDecodeError) as exc:
                skipped.append(f"{app}/{rel} ({type(exc).__name__})")
                continue
            raw = json.dumps(doc, sort_keys=True, ensure_ascii=False)
            sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            cur.execute(
                f"""INSERT INTO {_TABLE} (app, rel_path, doc, bytes, sha)
                    VALUES (%s,%s,%s::jsonb,%s,%s)
                    ON CONFLICT (rel_path, sha) DO NOTHING""",
                (app, f"{app}/{rel}", raw, size, sha),
            )
            if cur.rowcount:
                saved += 1
                if verbose:
                    print(f"  + {app}/{rel} ({size} bytes)")
            else:
                unchanged += 1
    result = {"saved": saved, "unchanged": unchanged, "skipped": skipped}
    if verbose:
        print(f"\n  snapshotted {saved} changed, {unchanged} unchanged")
        for s in skipped:
            print(f"  ! skipped {s}")
    return result


def status() -> None:
    ensure_table()
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            f"""SELECT rel_path, count(*), max(captured_at), max(bytes)
                FROM {_TABLE} GROUP BY rel_path ORDER BY rel_path"""
        )
        rows = cur.fetchall()
    if not rows:
        print("  nothing protected yet — run: json_store_guard.py snapshot")
        return
    print(f"  {'FILE':<52} {'SNAPS':>5}  {'BYTES':>7}  NEWEST")
    for rel, n, newest, size in rows:
        age = datetime.now() - newest
        flag = "  <-- STALE" if age.days >= 2 else ""
        print(f"  {rel:<52} {n:>5}  {size or 0:>7}  {newest:%Y-%m-%d %H:%M}{flag}")
    print(f"\n  {len(rows)} files protected")


def history(rel_path: str) -> None:
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            f"""SELECT id, captured_at, bytes, substr(sha,1,12) FROM {_TABLE}
                WHERE rel_path LIKE %s ORDER BY captured_at DESC LIMIT 25""",
            (f"%{rel_path}%",),
        )
        for r in cur.fetchall():
            print(f"  id={r[0]:<6} {r[1]:%Y-%m-%d %H:%M:%S}  {r[2] or 0:>7} bytes  sha {r[3]}")


def restore(rel_path: str, snap_id: int = None) -> None:
    """Write a snapshot back to disk. The existing file, if any, is preserved
    with a .pre-restore suffix — restoring must never destroy evidence either."""
    with _conn() as c, c.cursor() as cur:
        if snap_id:
            cur.execute(f"SELECT rel_path, doc FROM {_TABLE} WHERE id=%s", (snap_id,))
        else:
            cur.execute(
                f"""SELECT rel_path, doc FROM {_TABLE} WHERE rel_path LIKE %s
                    ORDER BY captured_at DESC LIMIT 1""",
                (f"%{rel_path}%",),
            )
        row = cur.fetchone()
    if not row:
        print(f"  no snapshot found for {rel_path}")
        return
    stored_rel, doc = row
    app, rel = stored_rel.split("/", 1)
    full = os.path.join(APPS[app], rel)
    if os.path.exists(full):
        backup = f"{full}.pre-restore.{datetime.now():%Y%m%d%H%M%S}"
        os.rename(full, backup)
        print(f"  existing file preserved as {os.path.basename(backup)}")
    os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
    tmp = f"{full}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, full)
    print(f"  RESTORED {full}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "snapshot"
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    if cmd == "snapshot":
        snapshot()
    elif cmd == "status":
        status()
    elif cmd == "history":
        history(arg or "")
    elif cmd == "restore":
        restore(arg or "", int(sys.argv[3]) if len(sys.argv) > 3 else None)
    else:
        print(__doc__)
