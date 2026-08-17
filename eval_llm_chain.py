#!/usr/bin/env python3
"""
Provider quality eval for EspaLuz Telegram (Familybot).

    python3 eval_llm_chain.py

Fifth in the fleet, and the ONLY one where the ordering rule is inverted.

For dragontrade and the Influencer the free providers go first: nobody is
waiting on a scheduled post, and a plainer tweet is survivable. EspaLuz is the
opposite. It is an emotionally intelligent expat assistant that evolves with the
family using it — a scared child asking about a dog, a parent mid-move, someone
practising in their second language. A mediocre reply here IS the product
failing, and these are paying users.

So the rule for EspaLuz is: ALWAYS REPLY, AT THE BEST QUALITY AVAILABLE.
Never defer, never "let me get back to you", never go silent — but never drop to
a weaker provider while a stronger one is answering either. The chain exists so
the tutor cannot go quiet, not to save money.

This eval therefore does not ask "did it answer". It asks whether the answer is
one Elena would be willing to send to a paying family:

  - BILINGUAL     — every reply must carry English and Spanish
  - WARM          — an emotional-support register, not a dictionary entry
  - CLEAN         — WhatsApp renders ** and # literally
  - SUBSTANTIAL   — a two-word reply is not tutoring
  - NO REFUSAL    — never "I can't help with that"

Providers are scored, not merely pass/failed, because the ORDER matters here:
the strongest goes first. Run this before changing any model id, and let the
scores pick the order rather than assuming.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_chain import PROFILE_QUALITY, PROVIDER_KEYS, _key, call_provider  # noqa: E402

# A real EspaLuz moment, not a synthetic prompt.
SYSTEM = (
    "You are EspaLuz, a warm bilingual family tutor for expat families in Panama. "
    "You remember each family and adapt to them. Reply in English AND Spanish. "
    "Be emotionally supportive and age-appropriate. Plain text only — no markdown."
)
USER = (
    "My 6-year-old daughter is crying because kids at her new school in Panama "
    "laughed at her Spanish today. She says she never wants to speak it again. "
    "Help me help her."
)
BUDGET = 800

# Accents alone are too narrow a test for "is there Spanish here".
#
# The first version of this check required an accented character or one word from
# a short list, and it false-flagged gemini as "NO SPANISH" on 2026-08-16 — a
# 4-runs-per-provider re-test then showed every provider was bilingual every
# time. The eval was wrong, not the model. Blaming a provider for a flaky
# assertion is how you end up removing a perfectly good one from the chain.
_ES_ACCENT = re.compile(r"[áéíóúñ¿¡]")
_ES_WORDS = re.compile(
    r"\b(que|para|con|tu|su|hija|hijo|puede|muy|bien|hablar|siente|corazon|"
    r"corazón|espanol|español|nina|niña|mama|mamá|papa|papá|amor|juntos)\b", re.I
)


def has_spanish(t: str) -> bool:
    """Accents, or enough Spanish words that it cannot be incidental."""
    return bool(_ES_ACCENT.search(t)) or len(_ES_WORDS.findall(t)) >= 3


WARM_HINT = re.compile(
    r"\b(understand|hard|brave|proud|feel|okay|normal|together|love|gentle|"
    r"entiendo|valiente|orgullos|juntos|siente|bien|corazón|tranquil)\w*", re.I
)
REFUSAL = re.compile(r"\b(I can'?t (help|assist)|I'?m (unable|not able)|as an AI)\b", re.I)
MARKDOWN = re.compile(r"\*\*|^#{1,6}\s|\n#{1,6}\s")


def score(text: str) -> tuple:
    """Return (points, problems). 5 points = safe to put first in the chain."""
    t = (text or "").strip()
    problems, pts = [], 0

    if len(t) >= 150:
        pts += 1
    else:
        problems.append(f"too short ({len(t)} chars)")

    if re.search(r"[A-Za-z]{4,}", t):
        pts += 1
    else:
        problems.append("no English")

    if has_spanish(t):
        pts += 1
    else:
        problems.append("NO SPANISH — breaks the bilingual promise")

    if WARM_HINT.search(t):
        pts += 1
    else:
        problems.append("no emotional register — reads like a dictionary")

    if REFUSAL.search(t):
        problems.append("REFUSED to help")
    else:
        # No markdown penalty on Telegram: main.py runs every reply through
        # strip_markdown_formatting() at send, and some sends intentionally use
        # parse_mode="Markdown". Penalising it here would demote good providers
        # for something the bot already handles.
        pts += 1

    return pts, problems


def main() -> int:
    print("=== EspaLuz quality eval — a real family moment, 800 tokens ===")
    print(f'    "{USER[:78]}..."\n')
    results = []
    for provider in ("claude", "openai", "gemini", "grok", "groq"):
        # _key() honours EspaLuz's CLAUDE_API_KEY fallback, exactly as the chain does.
        if not _key(PROVIDER_KEYS[provider]):
            print(f"  {provider:<8} SKIP   no {PROVIDER_KEYS[provider]}")
            continue
        try:
            t0 = time.time()
            # Familybot strips markdown itself at send (main.py strip_markdown_formatting),
            # and some Telegram sends use parse_mode="Markdown" where it is wanted. So the
            # chain does NOT strip, and markdown here is not a defect — see score().
            text = (call_provider(provider, SYSTEM, USER, BUDGET) or "").strip()
            ms = int((time.time() - t0) * 1000)
            pts, problems = score(text)
            results.append((pts, provider, ms, problems, text))
            flag = "✅" if pts == 5 else ("⚠️ " if pts >= 3 else "❌")
            detail = "; ".join(problems) if problems else "bilingual, warm, clean"
            print(f"  {provider:<8} {flag} {pts}/5  {ms:>5}ms  {detail}")
        except Exception as e:  # noqa: BLE001
            print(f"  {provider:<8} ❌ FAIL  {str(e)[:70]}")

    if not results:
        print("\n❌ no provider answered — EspaLuz would go silent")
        return 1

    # NOT a quality ranking — a FLOOR check.
    #
    # This scores five binary properties, so once a provider is bilingual, warm,
    # clean, substantial and non-refusing it hits 5/5 and ties with every other
    # provider that does. Sorting the ties by latency would put the FASTEST model
    # first, which is the opposite of what EspaLuz needs: on 2026-08-16 that
    # promoted groq (1.8s, weakest model) above claude (19.9s, strongest).
    #
    # A checklist can prove a provider is good ENOUGH. It cannot rank emotional
    # nuance. So the chain order in llm_chain.PROFILE_QUALITY is set by model
    # capability and stays fixed; this eval's job is to tell you if a provider
    # has dropped BELOW the floor and should be removed from the chain entirely.
    print("\n=== floor check (can this provider carry EspaLuz at all?) ===")
    for pts, provider, ms, _p, _t in sorted(results, key=lambda r: -r[0]):
        verdict = "meets the floor" if pts == 5 else "BELOW FLOOR — do not rely on it"
        print(f"  {provider:<8} {pts}/5  {ms:>6}ms  {verdict}")
    print(f"\n  chain order stays: {' -> '.join(PROFILE_QUALITY)}  (capability, not latency)")

    best = max(r[0] for r in results)
    # Ties break on CHAIN POSITION, not latency — for the same reason the floor
    # check above refuses to rank by speed. When all five hit 5/5, sorting ties
    # by latency labelled groq (1.8s, weakest) "the strongest provider" and
    # printed its sample, which is the one number this eval must never imply.
    # Show the reply from the provider that families actually reach first.
    print("\n=== sample from the highest-ranked provider that met the floor ===")
    top = sorted(results, key=lambda r: (-r[0], PROFILE_QUALITY.index(r[1])))[0]
    print(f"  [{top[1]}]\n  " + top[4][:340].replace("\n", "\n  "))

    if best < 5:
        print("\n⚠️  no provider scored 5/5 — check the prompt before shipping")
    print(f"\n✅ {len([r for r in results if r[0] >= 4])}/{len(results)} providers can carry EspaLuz quality")
    return 0


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    raise SystemExit(main())
