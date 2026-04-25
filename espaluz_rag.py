"""
EspaLuz RAG — Semantic Memory Retrieval
========================================
Embeds conversation turns using OpenAI text-embedding-3-small,
stores vectors in PostgreSQL (pgvector), retrieves semantically
similar past interactions before each Claude call.

Architecture:
  save_turn(session_id, role, content)
    → embed(content) → INSERT into espaluz_embeddings

  retrieve_context(session_id, query, top_k=3)
    → embed(query) → cosine similarity search → formatted string

Cost: ~$0.00002 per message (text-embedding-3-small = $0.02/1M tokens)
"""

import os
import json
import logging
import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)

DB_URL = os.getenv(
    'DATABASE_URL_UNIFIED',
    'postgresql://espaluz:EspaLuz2026!@localhost:5432/espaluz_unified'
)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
EMBED_MODEL = 'text-embedding-3-small'
EMBED_DIM = 1536


# ─── Embedding ─────────────────────────────────────────────────────────────

def _embed(text: str) -> list[float] | None:
    """Call OpenAI embedding API. Returns list of 1536 floats or None on error."""
    if not OPENAI_API_KEY:
        logger.warning('RAG: OPENAI_API_KEY not set')
        return None
    try:
        import requests
        resp = requests.post(
            'https://api.openai.com/v1/embeddings',
            headers={'Authorization': f'Bearer {OPENAI_API_KEY}',
                     'Content-Type': 'application/json'},
            json={'model': EMBED_MODEL, 'input': text[:8000]},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()['data'][0]['embedding']
    except Exception as e:
        logger.warning(f'RAG embed error: {e}')
        return None


# ─── DB helpers ────────────────────────────────────────────────────────────

def _conn():
    return psycopg2.connect(DB_URL)


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
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO espaluz_embeddings (session_id, role, content, embedding)
                    VALUES (%s, %s, %s, %s::vector)
                    """,
                    (session_id, role, content[:2000], json.dumps(vec))
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
        with _conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT role, content,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM espaluz_embeddings
                    WHERE session_id = %s
                      AND 1 - (embedding <=> %s::vector) > 0.75
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (json.dumps(vec), session_id, json.dumps(vec), json.dumps(vec), top_k)
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
