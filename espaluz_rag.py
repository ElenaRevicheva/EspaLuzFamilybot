"""
EspaLuz RAG — Semantic Memory Retrieval
========================================
Embeds conversation turns, stores vectors in PostgreSQL (pgvector), retrieves semantically similar past
interactions before each tutor reply. Shared by EspaLuzFamilybot and EspaLuzWhatsApp (same file in both repos,
same table) — change one, change both.

31 Oct 2026 — embeddings run LOCALLY on Oracle, free, always.
It used OpenAI text-embedding-3-small only. OpenAI ran out of credit on 23 Oct; the last vector anyone stored is
22 Oct 15:30 UTC, and every turn since logged "RAG embed error: 429" while main.py printed "RAG embeddings saved".
The bots had a memory they could not write to or search. No free embedding API is on our keys (Gemini 402
prepaid, xAI has no embedding model), so a small multilingual model (ES/EN/RU) runs inside the bot process via
fastembed (ONNX, no torch): $0, no quota, nothing to top up.

Why ONE model and not "paid first when funded" like the chat waterfall: vectors from two models cannot be
compared, so switching models with the balance would make half the memory unsearchable. Paid credit is spent
where it shows (the tutor's replies through llm_chain); here the free model is the right one every day.
Local vectors live in their own column, `embedding_local vector(384)`: the old `embedding` column is
vector(1536) with an ivfflat index built for OpenAI, and it keeps the 531 OpenAI rows of before 23 Oct untouched
(tagged `model='text-embedding-3-small'`). rag_backfill.py re-embeds the whole history with the local model.

  save_turn(session_id, role, content)       → embed → INSERT embedding_local (model = EMBED_MODEL)
  retrieve_context(session_id, query, top_k) → embed → cosine search over embedding_local
"""

import os
import json
import logging
import threading
import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)

DB_URL = os.getenv('DATABASE_URL_UNIFIED')  # set in .env; this module is imported lazily, long after load_dotenv()
EMBED_MODEL = os.getenv('RAG_EMBED_MODEL', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
EMBED_DIM = 384
# Cosine similarity of this model for "the same topic" sits lower than OpenAI's (0.75 was tuned for OpenAI).
MIN_SIMILARITY = float(os.getenv('RAG_MIN_SIMILARITY', '0.55'))
# One download shared by both bots.
_CACHE_DIR = os.getenv('RAG_MODEL_CACHE', '/home/ubuntu/.cache/espaluz-fastembed')

_model = None
_model_lock = threading.Lock()
_model_failed = False


def _get_model():
    """Load the local model once per process (first call downloads it, ~220 MB, into the shared cache)."""
    global _model, _model_failed
    if _model is not None or _model_failed:
        return _model
    with _model_lock:
        if _model is None and not _model_failed:
            try:
                from fastembed import TextEmbedding
                os.makedirs(_CACHE_DIR, exist_ok=True)
                _model = TextEmbedding(model_name=EMBED_MODEL, cache_dir=_CACHE_DIR)
                logger.info(f'RAG: local embedding model ready ({EMBED_MODEL})')
            except Exception as e:  # noqa: BLE001 — RAG is non-fatal; say so once, loudly
                _model_failed = True
                logger.error(f'RAG: local embedding model unavailable, semantic memory OFF: {e}')
    return _model


_schema_ready = False


def _ensure_schema():
    """Tag every row with the model that made it, so a search never compares vectors from different models."""
    global _schema_ready
    if _schema_ready:
        return
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE espaluz_embeddings ADD COLUMN IF NOT EXISTS model text "
                        "NOT NULL DEFAULT 'text-embedding-3-small'")
            cur.execute(f"ALTER TABLE espaluz_embeddings ADD COLUMN IF NOT EXISTS embedding_local vector({EMBED_DIM})")
        conn.commit()
    _schema_ready = True


# ─── Embedding ─────────────────────────────────────────────────────────────

def _embed(text: str) -> list[float] | None:
    """Embed one text with the local model. Returns EMBED_DIM floats or None on error."""
    model = _get_model()
    if model is None or not (text or '').strip():
        return None
    try:
        return [float(x) for x in next(iter(model.embed([text[:2000]])))]
    except Exception as e:  # noqa: BLE001
        logger.warning(f'RAG embed error: {e}')
        return None


# ─── DB helpers ────────────────────────────────────────────────────────────

def _conn():
    # Resolved at call time too: an import before load_dotenv() must not leave RAG without a database for the
    # life of the process (the old server copy hid that case behind a hardcoded password; never again).
    return psycopg2.connect(DB_URL or os.getenv('DATABASE_URL_UNIFIED'))


# ─── Public API ────────────────────────────────────────────────────────────

def save_turn(session_id: str, role: str, content: str) -> bool:
    """
    Embed a conversation turn and store in espaluz_embeddings.
    Called after every user message and bot reply.
    Returns True on success, False on any error (non-fatal).
    """
    if not content or not session_id:
        return False
    vec = _embed(content)
    if vec is None:
        return False
    try:
        _ensure_schema()
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO espaluz_embeddings (session_id, role, content, embedding_local, model)
                    VALUES (%s, %s, %s, %s::vector, %s)
                    """,
                    (session_id, role, content[:2000], json.dumps(vec), EMBED_MODEL)
                )
            conn.commit()
        return True
    except Exception as e:
        logger.warning(f'RAG save error: {e}')
        return False


def retrieve_context(session_id: str, query: str, top_k: int = 3) -> str:
    """
    Embed query, search espaluz_embeddings for semantically similar past turns.
    Returns formatted string ready to inject into system prompt.
    Empty string if nothing found or any error.
    """
    if not query or not session_id:
        return ''
    vec = _embed(query)
    if vec is None:
        return ''
    try:
        _ensure_schema()
        with _conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT role, content,
                           1 - (embedding_local <=> %s::vector) AS similarity
                    FROM espaluz_embeddings
                    WHERE session_id = %s
                      AND model = %s
                      AND embedding_local IS NOT NULL
                      AND 1 - (embedding_local <=> %s::vector) > %s
                    ORDER BY embedding_local <=> %s::vector
                    LIMIT %s
                    """,
                    (json.dumps(vec), session_id, EMBED_MODEL, json.dumps(vec), MIN_SIMILARITY,
                     json.dumps(vec), top_k)
                )
                rows = cur.fetchall()

        if not rows:
            return ''

        lines = ['Semantically relevant past interactions:']
        for r in rows:
            role_label = 'User' if r['role'] == 'user' else 'EspaLuz'
            sim = round(r['similarity'] * 100)
            lines.append(f'  [{sim}% match] {role_label}: {r["content"][:200]}')
        return '\n'.join(lines)

    except Exception as e:
        logger.warning(f'RAG retrieve error: {e}')
        return ''


def get_session_id_for_user(platform: str, db_user_id: int) -> str:
    """
    Returns the UUID session_id that LangChain uses for this user.
    LangChain generates: uuid5(NAMESPACE_DNS, f'{platform}_{db_user_id}')
    We use the same formula so embeddings and LangChain rows share session scope.
    """
    import uuid
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f'{platform}_{db_user_id}'))
