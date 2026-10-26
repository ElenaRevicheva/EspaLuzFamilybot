"""
Provider chain for EspaLuz Telegram (Familybot) — the QUALITY profile.

Same rule as the WhatsApp twin, because it is the same product and the same
paying families: ALWAYS REPLY, AT THE BEST QUALITY AVAILABLE. Never defer,
never go silent, and never drop to a weaker provider while a stronger one is
still answering. The chain exists so the tutor cannot go quiet — not to save
money. That is the opposite of the bulk profiles used by dragontrade and the
Influencer, where nobody is waiting and cost leads.

IMPORTANT — this module does NOT strip markdown, unlike the WhatsApp copy.
Familybot already runs every reply through `strip_markdown_formatting()` at
send time (defined in main.py, applied at both `bot.send_message` sites), and
Telegram also sends some messages with `parse_mode="Markdown"` where the
formatting is wanted. Stripping here would either duplicate that work or
destroy intentional formatting. Reuse what the bot already does; do not add a
second stripper.

Why this exists now (2026-08-16): Groq retired llama-3.3-70b-versatile, and
`_groq_model()` in main.py still names it as its default — safe only because
GROQ_MODEL is set in this repo's .env. Its replacements are REASONING models
that spend a small max_tokens budget thinking and return "", so the Groq link
in the fallback ladder had quietly become the least reliable one.

The existing ladder was already good — Claude → Groq → gpt-4o-mini → gpt-4.
This adds Gemini and Grok so a bad day for two providers cannot silence the
tutor, and puts the model ids behind env vars so the next retirement is a
config change rather than a code hunt.
"""
import json
import os
import urllib.error
import urllib.request
from typing import Iterable, List, Optional, Tuple

# Emotional replies need room, and reasoning models emit nothing below ~300.
MIN_TOKENS = 600

# Strongest first. Confirm with eval_llm_chain.py before reordering.
# 26 Oct 2026 ORDER RULE (Elena): all five providers wired; free ones first (Gemini, Groq), then Grok, then OpenAI — no
# regular money to top it up, it refuses in ~0.1 s without credit — and Claude by money. Nothing switched off.
PROFILE_QUALITY: Tuple[str, ...] = ("claude", "gemini", "groq", "grok", "openai")

# What the post-Claude fallback uses: Claude is excluded because it is the
# primary that just failed, and retrying it costs ~19s before failing again.
PROFILE_FALLBACK: Tuple[str, ...] = ("gemini", "groq", "grok", "openai")

PROVIDER_KEYS = {
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "grok": "XAI_API_KEY",
    "groq": "GROQ_API_KEY",
}

_URLS = {
    "claude": "https://api.anthropic.com/v1/messages",
    "openai": "https://api.openai.com/v1/chat/completions",
    "grok": "https://api.x.ai/v1/chat/completions",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
}


def _key(name: str) -> str:
    """EspaLuz uses CLAUDE_API_KEY for Anthropic (separate account from cto-aipa)."""
    v = os.environ.get(name, "").strip()
    if v:
        return v
    if name == "ANTHROPIC_API_KEY":
        return os.environ.get("CLAUDE_API_KEY", "").strip()
    return ""


def _model(provider: str) -> str:
    return {
        # Sonnet, not Haiku — this is the emotional-intelligence surface.
        "claude": os.environ.get("CLAUDE_CHAIN_MODEL", "").strip() or "claude-sonnet-4-5-20250929",
        # gpt-4o, not mini: mini noticeably flattens warmth on this prompt shape.
        "openai": os.environ.get("OPENAI_CHAIN_MODEL", "").strip() or "gpt-4o",
        "gemini": os.environ.get("GEMINI_MODEL", "").strip() or "gemini-2.5-flash",
        "grok": os.environ.get("XAI_MODEL", "").strip() or "grok-4.20-0309-non-reasoning",
        # THE one Groq switch, same GROQ_MODEL env var as the rest of the fleet.
        "groq": os.environ.get("GROQ_MODEL", "").strip() or "openai/gpt-oss-120b",
    }[provider]


def _post(url: str, headers: dict, body: dict, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json", **headers},
    )
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())


def call_provider(provider: str, system: Optional[str], user: str, max_tokens: int) -> str:
    """One provider, one attempt. Raises on transport/HTTP failure."""
    key = _key(PROVIDER_KEYS[provider])
    if not key:
        raise RuntimeError(f"no {PROVIDER_KEYS[provider]}")
    model = _model(provider)

    if provider == "claude":
        body = {"model": model, "max_tokens": max_tokens, "temperature": 0.7,
                "messages": [{"role": "user", "content": user}]}
        if system:
            body["system"] = system[:14000]
        data = _post(_URLS["claude"], {"x-api-key": key, "anthropic-version": "2023-06-01"}, body)
        return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")

    if provider == "gemini":
        # thinkingBudget:0 stops a REASONING model spending the whole budget
        # thinking and returning a reply truncated mid-sentence. PLAIN models
        # reject the parameter with 400, so try it, then retry without rather
        # than maintaining a list of which models are plain.
        def _call(with_thinking: bool) -> str:
            body: dict = {
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {
                    "maxOutputTokens": max_tokens, "temperature": 0.7,
                    **({"thinkingConfig": {"thinkingBudget": 0}} if with_thinking else {}),
                },
            }
            if system:
                body["systemInstruction"] = {"parts": [{"text": system[:14000]}]}
            url = (f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
                   f":generateContent?key={key}")
            data = _post(url, {}, body)
            cands = data.get("candidates") or [{}]
            parts = (cands[0].get("content") or {}).get("parts") or [{}]
            return parts[0].get("text") or ""

        try:
            return _call(True)
        except urllib.error.HTTPError as e:
            if e.code != 400:
                raise
            return _call(False)

    # openai / grok / groq are OpenAI-compatible
    messages = ([{"role": "system", "content": system[:14000]}] if system else []) + \
               [{"role": "user", "content": user}]
    headers = {"Authorization": "Bearer " + key}
    if provider == "groq":
        # Cloudflare fronts api.groq.com and 403s the default urllib User-Agent.
        headers["User-Agent"] = "EspaLuz/1.0 (+https://aideazz.xyz)"
    data = _post(_URLS[provider], headers,
                 {"model": model, "messages": messages,
                  "max_tokens": max_tokens, "temperature": 0.7})
    return data["choices"][0]["message"]["content"] or ""


def complete(system: Optional[str], user: str, max_tokens: int = 1000,
             order: Iterable[str] = PROFILE_QUALITY) -> Tuple[str, List[str]]:
    """Walk the chain until a provider returns a real reply.

    The default order is the FULL chain, matching the WhatsApp twin. Callers on
    a post-Claude path must pass `order=PROFILE_FALLBACK` explicitly — every one
    of them does. Defaulting to the fallback profile instead would mean a future
    caller reaching for a primary path silently skipped Claude, the strongest
    provider, and nothing would look broken.

    Returns (text, errors). An EMPTY or whitespace reply counts as a FAILURE and
    advances the chain: handing "" back would make EspaLuz go silent on a family,
    which is the one outcome not allowed here.

    Empty text on return means every provider failed — the caller should then
    fall back to its own warm holding message rather than sending nothing.
    """
    budget = max(int(max_tokens), MIN_TOKENS)
    errors: List[str] = []
    for provider in order:
        try:
            text = call_provider(provider, system, user, budget)
            if text and text.strip():
                if errors:
                    print(f"[llm_chain] Familybot replied via {provider} after {len(errors)} failure(s)")
                return text, errors
            errors.append(f"{provider}: empty response")
        except Exception as e:  # noqa: BLE001 — any failure must advance the chain
            errors.append(f"{provider}: {str(e)[:120]}")
    return "", errors
