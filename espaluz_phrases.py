# 19 Nov 2026 - TWIN of ascent-saas-builder supabase/functions/_shared/phrases.ts (phrasesIn), line for line.
# ONE phrase finder for the whole brain: the web/WhatsApp/Telegram progress (submit-progress), the dashboard, and now
# the bots' own vocabulary for /review (Elena: "saving word meanings for /review"). It finds the Spanish phrases
# EspaLuz really taught in a reply, WITH their English. Change one, change both - the parity test runs both on the
# same real replies (cto-aipa docs/espaluz/REVIEW_MEANINGS_2026-11-19.md).
import re

SPANISH = re.compile(r"[¿¡áéíóúñ]|\b(el|la|los|las|por|para|que|puedes|dónde|cómo|quiero|tengo|necesito|gracias|favor|es|está|una?|mi|mis|se|vamos|no)\b", re.I)
ENGLISH = re.compile(r"\b(the|is|are|you|your|my|i|it|to|of|we|can|what|where|how|this|please|do|need|he|she|go|let's|time|name|in|at|with|a)\b", re.I)
PRON = re.compile(r"[A-Z]{2,}-|‑|\b[A-Z]{3,}\b.*-|[ɲ]")


def _clean(s):
    s = re.sub(r"\*+", "", s)
    s = re.sub(r'^[\s"“”\'-]+|[\s"“”\']+$', "", s)
    return re.sub(r"\s+", " ", s).strip()


def phrases_in(text, max_n=6):
    """[{'es': ..., 'en': ...}] - the Spanish phrases taught in one reply, with their English ('' when not given)."""
    out = []

    def add(es, en=None, shaped=False):
        es = _clean(es[es.rfind(": ") + 2:] if ": " in es else es)
        es = re.sub(r"\s*\[[^\]]*\]?\s*$", "", es).strip()
        en = _clean(en or "")
        en = re.sub(r"^[(\s]+|[)\s]+$", "", en)
        en = re.sub(r"([?!]).*$", r"\1", en)
        if en and (PRON.search(en) or not ENGLISH.search(en)):
            en = ""
        if len(es) < 4 or len(es) > 90 or not (SPANISH.search(es) or (shaped and en)) or "…" in es:
            return
        out.append({"es": es, "en": en})

    body = re.sub(r"\[VIDEO SCRIPT START\][\s\S]*?(\[VIDEO SCRIPT END\]|$)", "", str(text or ""))
    for m in re.finditer(r'\*{0,2}[“"]([^”"\n]{4,90})[”"]\*{0,2}\s*(?:\[[^\]\n]{2,90}\]\s*[-–]\s*([^.\n(–]{3,90})|\(([^)\n]{3,90})\))', body):
        add(m.group(1), m.group(2) if m.group(2) is not None else m.group(3))
    for m in re.finditer(r'(?:^|\n|:\s)\s*(¿?¡?[A-Za-zÁÉÍÓÚÑáéíóúñ][^\[\n“"]{2,80}?)\s*\[[^\]\n]{3,90}\]\s*[-–]\s*([^.\n(]{3,90})', body):
        add(m.group(1), m.group(2))
    for m in re.finditer(r'(?:^|\n)\s*-\s+(¿?¡?[^\n“"–]{3,80}?)\s+[–-]\s+([A-Z][^\n(.]{3,90})', body):
        add(m.group(1), m.group(2))
    for m in re.finditer(r'(?:^|\s)\d[.)]\s+(¿?¡?[A-Za-zÁÉÍÓÚÑáéíóúñ][^\n(“"\[]{2,80}?)\s*\(([^)\n]{2,90})\)\s*[-–]\s*(\[[^\]\n]*\]?|[^.\n(]{3,90})', body):
        if m.group(1) == m.group(1).upper():
            continue
        in_brackets = _clean(m.group(2))
        if not PRON.search(in_brackets) and not re.search(r"\w-\w+-\w", in_brackets) and ENGLISH.search(in_brackets):
            english = in_brackets
        else:
            english = "" if m.group(3).startswith("[") else m.group(3)
        add(m.group(1), english, True)
    # 19 Nov 2026: "Quedo pendiente" = I'll be watching for it. · "Por duelo" [por DWEH-loh] = "Due to mourning"
    # Same day: "Un café, por favor." (oon kah-FEH) - "A coffee, please." - pronunciation in ROUND brackets, then the English.
    for m in re.finditer(r'[“"]([^”"\n]{4,90})[”"]\*{0,2}\s*(?:[\[(][^\])\n]{2,90}[\])]\s*)?(?:=|[-–])\s*[“"]?([^”"\n.!?]{3,90}[!?]?)', body):
        add(m.group(1), m.group(2))
    # A phrase found twice keeps the copy WITH its English (the first pattern may have read only its pronunciation).
    best = {}
    for p in out:
        k = p["es"].lower()
        if k not in best or (not best[k]["en"] and p["en"]):
            best[k] = p
    return list(best.values())[:max_n]
