"""EspaLuz cards in Telegram - live widgets inside the chat (Bot API 10.4, 9 Nov 2026). Elena, 10 Nov: "integrate as
many cards as makes sense". Three cards, each built BY CODE from data we already keep - no model writes a card, so a card
cannot invent anything:

  🌴 Tu camino / Your road   family notebook (kids-memory facts_get + stars): road stage, class turns, stars, how many
                              things EspaLuz remembers (a count, never a note's text). Updated IN PLACE after a lesson.
  🌎 Vida en <país>           the CHECKED lines of the family's belonging pack (belonging/<country>.json), one per topic.
  💬 Palabras locales         local expressions and greetings from the same pack, as tap-to-reveal flash cards.

A widget works only in the private chat with the bot (production, Nov 2026); an app without widgets shows the caption,
so every caption says what the card is. If sendWidget fails, the family gets a plain-text version - never nothing.
Log lines: `🃏 card sent kind=<k>`, `🃏 card updated kind=road`, `🃏 card fallback kind=<k>`.
"""
import json
import os
import re
import threading
import zlib
from datetime import datetime, timezone

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
SAAS = "https://euyidvolwqmzijkfrplh.supabase.co/functions/v1/kids-memory"
APP = "https://app.espaluz.lat"
CARDS_LABEL = "🃏 Tarjetas · Cards"
_ROAD_FILE = os.path.join(HERE, ".road_cards.json")  # telegram user id -> message_id of the newest road card
_lock = threading.Lock()

# moved_when answers (web questionnaire, ascent FamilyProfileDialog.tsx) -> the stage of the long road. -1 = not answered.
STAGE = {"Still planning the move": 0, "Traveling - still looking for my place": 0, "Less than 6 months": 1,
         "6 to 12 months": 2, "1 to 3 years": 2, "More than 3 years": 3}

SECTION_ES = {"rhythm_of_the_year": "El año · The year", "holidays": "Fiestas · Holidays",
              "greetings_and_courtesy": "Saludos · Greetings", "time": "La hora · Time",
              "family_and_friends": "Familia · Family", "school_life": "La escuela · School",
              "food_and_table": "La mesa · Food", "everyday_life": "El día a día · Everyday life",
              "local_expressions": "Palabras · Words", "newcomers_find_hard": "Lo difícil · What is hard",
              "folk_culture": "Cultura · Culture"}

_CSS = """<style>
h3{margin:0}.h{color:var(--tg-theme-hint-color);font-size:.85em}
.b{display:flex;gap:6px;margin-top:8px}.b button{flex:1}
</style>"""

_JS_COMMON = """const W=window.TelegramWidget;
const e=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const $=id=>document.getElementById(id);"""

# ---------- 1. Your road ----------
ROAD_HTML = _CSS + r"""<style>
.r{display:flex;gap:4px;margin:10px 0 3px}.r i{flex:1;height:6px;border-radius:3px;background:var(--tg-theme-secondary-bg-color)}
.r i.on{background:var(--tg-theme-button-color)}
.l{display:flex;justify-content:space-between;font-size:.7em;color:var(--tg-theme-hint-color)}.l .on{color:var(--tg-theme-accent-text-color);font-weight:600}
.g{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:10px 0 0;text-align:center;font-size:.8em}
.g div{background:var(--tg-theme-secondary-bg-color);border-radius:10px;padding:6px 2px}.g b{display:block;font-size:1.5em}
</style>
<div id="c"><h3>EspaLuz</h3></div>
<div class="b"><button id="k">Kids classroom</button><button id="f">My family</button></div>
<script>""" + _JS_COMMON + r"""
const S=[["Elegir","Choosing"],["Llegar","Arriving"],["Asentarse","Settling in"],["Pertenecer","Belonging"]];
function r(){let d={};try{d=JSON.parse(W.chatData)||{}}catch(x){}
if(d.x){$("c").innerHTML="<h3>Tu camino · Your road</h3><div class='h' style='margin-top:6px'>Link this chat to your family in the app, and your road, your child's stars and what EspaLuz remembers show up here.</div>";return}
const s=d.s??-1,m=d.m||[];
let h="<h3>Tu camino · Your road</h3><div class='h'>"+(d.c?e(d.c)+" · ":"")+(m.length?m.map(x=>e(x[0])+(x[1]?" ("+x[1]+")":"")).join(", "):"Tell EspaLuz who is with you")+"</div>";
h+="<div class='r'>"+S.map((x,i)=>"<i class='"+(i<=s?"on":"")+"'></i>").join("")+"</div><div class='l'>"+S.map((x,i)=>"<span class='"+(i==s?"on":"")+"'>"+x[0]+"</span>").join("")+"</div>";
h+="<div class='h' style='margin-top:4px'>"+(s>=0?"Now: "+S[s][1]:"Where are you on the road? Tell EspaLuz")+"</div>";
h+="<div class='g'><div><b>"+(d.t??0)+"</b>class turns<br>this week</div><div><b>"+(d.st??0)+"</b>stars<br>all time</div><div><b>"+(d.n??0)+"</b>things she<br>remembers</div></div>";
if(d.ls)h+="<div class='h' style='margin-top:6px'>Last class: "+e(d.ls)+"</div>";
if(d.u)h+="<div class='h'>Updated "+e(d.u)+"</div>";
$("c").innerHTML=h}
$("k").onclick=()=>W.openLink("APP/classroom");
$("f").onclick=()=>W.openLink("APP/dashboard");
W.onEvent("chatDataChanged",r);r();W.ready&&W.ready();
</script>""".replace("APP", APP)

# ---------- 2 + 3. Deck cards (life facts / local words): the items are baked into the HTML at send time ----------
DECK_HTML = _CSS + r"""<style>
.t{font-size:.75em;color:var(--tg-theme-accent-text-color);font-weight:600;margin-top:8px}
.es{font-size:1.15em;font-weight:600;margin:4px 0;user-select:text;-webkit-user-select:text}
.tx{margin:4px 0;min-height:2.6em}.n{text-align:right}
</style>
<h3>TITLE</h3><div class="h">SUB</div><div id="c"></div>
<div class="b"><button id="p">◀ Atrás</button><button id="v">REVEAL</button><button id="n">Más ▶</button></div>
<script>""" + _JS_COMMON + r"""
const D=DATA,F=FLIP;let i=0,o=!F;
function r(){const x=D[i];o=o||!F;
$("c").innerHTML="<div class='t'>"+e(x[0])+"</div>"+(x[1]?"<div class='es'>"+e(x[1])+"</div>":"")+"<div class='tx'>"+(o?e(x[2]):"<span class='h'>Tap REVEAL</span>")+"</div><div class='h n'>"+(i+1)+" / "+D.length+"</div>";
$("v").disabled=o}
$("p").onclick=()=>{i=(i+D.length-1)%D.length;o=false;r()};
$("n").onclick=()=>{i=(i+1)%D.length;o=false;r()};
$("v").onclick=()=>{o=true;r()};
r();W.ready&&W.ready();
</script>"""


def _pack(country):
    from espaluz_enhancements import belonging_country
    key = belonging_country(country or "panama")
    path = os.path.join(HERE, "belonging", f"{key}.json")
    if not os.path.exists(path):
        key, path = "panama", os.path.join(HERE, "belonging", "panama.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _checked(pack, sections):
    return [(s, i) for s in sections for i in pack.get("sections", {}).get(s, []) if i.get("status") == "checked"]


def _fit(build, items):
    """Drop items from the end until the HTML fits Telegram's limit (4096 bytes after zlib level 9)."""
    while items:
        html = build(items)
        if len(zlib.compress(html.encode(), 9)) <= 4000:
            return html
        items = items[:-1]
    return None


def _deck_html(title, sub, items, flip, reveal):
    data = json.dumps(items, ensure_ascii=False).replace("</", r"<\/")
    html = DECK_HTML
    if not flip:  # a facts deck has nothing to reveal
        for cut in ('<button id="v">REVEAL</button>', '$("v").disabled=o', '$("v").onclick=()=>{o=true;r()};'):
            html = html.replace(cut, "")
    # DATA last: an item's text must never be mistaken for a placeholder
    return (html.replace("TITLE", title).replace("SUB", sub).replace("REVEAL", reveal)
            .replace("FLIP", "true" if flip else "false").replace("DATA", data))


def life_card(country):
    """One checked fact per topic, in the order a newcomer lives them; then more from the busiest topics."""
    pack = _pack(country)
    order = ["greetings_and_courtesy", "time", "everyday_life", "family_and_friends", "school_life", "food_and_table",
             "rhythm_of_the_year", "holidays", "newcomers_find_hard", "folk_culture"]
    rows, seen = [], set()
    for rnd in range(3):
        for s in order:
            items = [i for i in pack.get("sections", {}).get(s, []) if i.get("status") == "checked"]
            if rnd < len(items) and items[rnd]["text"] not in seen:
                seen.add(items[rnd]["text"])
                rows.append([SECTION_ES.get(s, s), items[rnd].get("es") or "", items[rnd]["text"][:280]])
    n_src = len(pack.get("sources") or {})
    sub = f"{len(rows)} checked facts · {n_src} sources · {pack.get('checked_on', '')}"
    html = _fit(lambda it: _deck_html(f"Vida en {pack['name']} · Life in {pack['name']}", sub, it, False, "·"), rows)
    caption = (f"🌎 Vida en {pack['name']} · Life in {pack['name']}: how people here greet, keep time, eat and celebrate. "
               "Only checked facts. Tap Más ▶ for the next one.")
    return html, caption, pack["name"]


def _phrase(text):
    m = re.search(r"['‘“\"]([^'’”\"]{2,40})['’”\"]", text)
    return m.group(1) if m else ""


def words_card(country):
    pack = _pack(country)
    rows = []
    for s, i in _checked(pack, ["local_expressions", "greetings_and_courtesy"]):
        front = i.get("es") or _phrase(i["text"])
        if front:
            rows.append([SECTION_ES.get(s, s), front, i["text"][:280]])
    html = _fit(lambda it: _deck_html(f"Palabras de {pack['name']} · Local words", "Read it, guess it, then tap Ver.",
                                      it, True, "Ver · Show"), rows)
    caption = f"💬 Palabras de {pack['name']} · Local words: what people really say, and when. Tap Ver to see the meaning."
    return html, caption, pack["name"]


def _family(uid):
    h = {"Authorization": f"Bearer {os.environ.get('SUPABASE_ANON_KEY', '')}", "x-espaluz-bot-secret": os.environ.get("ESPALUZ_BOT_SECRET", "")}
    f = requests.post(SAAS, json={"mode": "facts_get", "telegram_user_id": str(uid)}, headers=h, timeout=20).json()
    s = requests.post(SAAS, json={"mode": "stars", "telegram_user_id": str(uid)}, headers=h, timeout=20).json() if f.get("linked") else {}
    return f, s


def road_state(uid):
    f, s = _family(uid)
    if not f.get("linked"):
        return json.dumps({"x": 1}), f
    p = f.get("profile") or {}
    d = {"c": str(p.get("country_now") or "").replace("_", " ").title()[:30], "s": STAGE.get(p.get("moved_when"), -1),
         "m": [[str(x.get("name") or "")[:20], x.get("age")] for x in (f.get("members") or [])[:6]],
         "t": int(f.get("lesson_turns") or 0), "st": int(s.get("stars") or 0), "n": len(f.get("facts") or []),
         "ls": str((f.get("lessons") or [""])[0])[:80], "u": datetime.now(timezone.utc).strftime("%d %b %H:%M UTC")}
    out = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    while len(out.encode()) > 1024 and d["m"]:
        d["m"].pop()
        out = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    return out, f


def road_text(state):
    d = json.loads(state)
    if d.get("x"):
        return f"🌴 Tu camino · Your road\nLink this chat to your family in the app: {APP}/dashboard"
    names = ", ".join(m[0] for m in d.get("m", [])) or "-"
    return (f"🌴 Tu camino · Your road\n{d.get('c') or ''} · {names}\n"
            f"Class turns this week: {d.get('t', 0)} · Stars: {d.get('st', 0)} · Things EspaLuz remembers: {d.get('n', 0)}")


def _api(method, payload):
    r = requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/{method}", json=payload, timeout=20)
    return r.json()


def _roads():
    try:
        with open(_ROAD_FILE) as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001 - missing file = no cards yet
        return {}


def _save_road(uid, message_id):
    with _lock:
        d = _roads()
        d[str(uid)] = message_id
        with open(_ROAD_FILE, "w") as fh:
            json.dump(d, fh)


def send_card(bot, chat_id, uid, kind, country=""):
    """Send one card; on any widget failure send the text version. Returns the widget message_id or None."""
    try:
        if kind == "road":
            state, _ = road_state(uid)
            html, data, caption, fallback = ROAD_HTML, state, "🌴 Tu camino con EspaLuz · Your family's road", road_text(state)
        else:
            html, caption, _name = (life_card if kind == "life" else words_card)(country)
            data, fallback = None, caption
        if not html:
            raise ValueError("no items fit")
        payload = {"chat_id": int(chat_id), "html": html, "caption": caption}
        if data:
            payload["chat_data"] = data
        j = _api("sendWidget", payload)
        if j.get("ok"):
            mid = j["result"]["message_id"]
            if kind == "road":
                _save_road(uid, mid)
            print(f"🃏 card sent kind={kind} message_id={mid}", flush=True)
            return mid
        raise RuntimeError(j.get("description"))
    except Exception as e:  # noqa: BLE001 - a card is a bonus: the family always gets the text
        print(f"🃏 card fallback kind={kind}: {str(e)[:160]}", flush=True)
        try:
            bot.send_message(chat_id, fallback if "fallback" in locals() else "🃏 EspaLuz")
        except Exception:  # noqa: BLE001
            pass
        return None


def refresh_road(uid):
    """After a lesson: the family's newest road card updates in place (no new message). A linked family without a card
    gets its first one here, ONCE (10 Nov: the in-place update only helps a family that has a card); after that, never a
    new message - only the same card changing."""
    mid = _roads().get(str(uid))
    if not mid:
        state, f = road_state(uid)
        if not f.get("linked"):
            return False
        j = _api("sendWidget", {"chat_id": int(uid), "html": ROAD_HTML, "chat_data": state,
                                "caption": "🌴 Tu camino con EspaLuz · Your family's road. Se actualiza solo después de cada clase · "
                                           "It updates itself after every class."})
        if j.get("ok"):
            _save_road(uid, j["result"]["message_id"])
            print(f"🃏 card sent kind=road first=1 message_id={j['result']['message_id']}", flush=True)
            return True
        print(f"🃏 card first road failed: {j.get('description')}", flush=True)
        return False
    try:
        state, _ = road_state(uid)
        j = _api("editMessageWidgetData", {"chat_id": int(uid), "message_id": int(mid), "chat_data": state})
        if j.get("ok"):
            print(f"🃏 card updated kind=road message_id={mid}", flush=True)
            return True
        if "not modified" in str(j.get("description")):  # same numbers as on screen: nothing to change, not an error
            print(f"🃏 card unchanged kind=road message_id={mid}", flush=True)
            return True
        print(f"🃏 card update failed kind=road: {j.get('description')}", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"🃏 card update failed kind=road: {str(e)[:160]}", flush=True)
    return False


def menu_markup():
    from telebot import types
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🌴 Tu camino · Your road", callback_data="card:road"),
          types.InlineKeyboardButton("🌎 Vida local · Local life", callback_data="card:life"),
          types.InlineKeyboardButton("💬 Palabras locales · Local words", callback_data="card:words"))
    return m


MENU_TEXT = "🃏 Tarjetas de EspaLuz · EspaLuz cards. ¿Cuál? · Which one?"


if __name__ == "__main__":  # size check for every country, sends nothing
    from dotenv import load_dotenv
    load_dotenv(os.path.join(HERE, ".env"))
    print("road", len(zlib.compress(ROAD_HTML.encode(), 9)))
    for f in sorted(os.listdir(os.path.join(HERE, "belonging"))):
        c = f[:-5]
        lh, _, _ = life_card(c)
        wh, _, _ = words_card(c)
        print(c, "life", lh and len(zlib.compress(lh.encode(), 9)), lh and lh.count("\",[") , "words",
              wh and len(zlib.compress(wh.encode(), 9)))
