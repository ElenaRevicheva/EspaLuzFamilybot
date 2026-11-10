"""EspaLuz "Your family's road" card - a Telegram widget (Bot API 10.4, 9 Nov 2026), first try 10 Nov 2026.

One live card inside the chat instead of a new message each time: the code (HTML) is fixed when sent, the numbers are
the widget's chat state, which this script can change in place later (--edit <message_id>), with no new message.

Built by code from kids-memory facts_get + stars (the same notebook web/WhatsApp/Telegram read): no model writes it,
so nothing on it can be invented. Private notes are never shown, only how many notes EspaLuz keeps.

Run on Oracle from ~/EspaLuzFamilybot (reads .env; does NOT touch the running bot):
  venv/bin/python family_road_widget.py --to <telegram_user_id>            # send a new card
  venv/bin/python family_road_widget.py --to <id> --edit <message_id>      # update the numbers in place
  venv/bin/python family_road_widget.py --to <id> --dry                    # print state + sizes, send nothing
Widgets work only in the private chat with the bot (production, Nov 2026). Older Telegram apps show the caption.
"""
import argparse, json, os, sys, zlib
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
SAAS = "https://euyidvolwqmzijkfrplh.supabase.co/functions/v1/kids-memory"
APP = "https://app.espaluz.lat"

# moved_when answers (web questionnaire, FamilyProfileDialog.tsx) -> the stage of the long road. -1 = not answered.
STAGE = {"Still planning the move": 0, "Traveling - still looking for my place": 0, "Less than 6 months": 1,
         "6 to 12 months": 2, "1 to 3 years": 2, "More than 3 years": 3}

HTML = r"""<style>
h3{margin:0}.h{color:var(--tg-theme-hint-color);font-size:.85em}
.r{display:flex;gap:4px;margin:10px 0 3px}.r i{flex:1;height:6px;border-radius:3px;background:var(--tg-theme-secondary-bg-color)}
.r i.on{background:var(--tg-theme-button-color)}
.l{display:flex;justify-content:space-between;font-size:.7em;color:var(--tg-theme-hint-color)}.l .on{color:var(--tg-theme-accent-text-color);font-weight:600}
.g{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:10px 0;text-align:center;font-size:.8em}
.g div{background:var(--tg-theme-secondary-bg-color);border-radius:10px;padding:6px 2px}.g b{display:block;font-size:1.5em}
.b{display:flex;gap:6px}.b button{flex:1}
</style>
<div id="c"><h3>EspaLuz</h3></div>
<div class="b"><button id="k">Kids classroom</button><button id="f">My family</button></div>
<script>
const W=window.TelegramWidget;
const S=[["Elegir","Choosing"],["Llegar","Arriving"],["Asentarse","Settling in"],["Pertenecer","Belonging"]];
const e=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function r(){let d={};try{d=JSON.parse(W.chatData)||{}}catch(x){}
const s=d.s??-1,m=d.m||[];
let h="<h3>Tu camino · Your road</h3><div class='h'>"+(d.c?e(d.c)+" · ":"")+(m.length?m.map(x=>e(x[0])+(x[1]?" ("+x[1]+")":"")).join(", "):"Tell EspaLuz who is with you")+"</div>";
h+="<div class='r'>"+S.map((x,i)=>"<i class='"+(i<=s?"on":"")+"'></i>").join("")+"</div><div class='l'>"+S.map((x,i)=>"<span class='"+(i==s?"on":"")+"'>"+x[0]+"</span>").join("")+"</div>";
h+="<div class='h' style='margin-top:4px'>"+(s>=0?"Now: "+S[s][1]:"Where are you on the road? Tell EspaLuz")+"</div>";
h+="<div class='g'><div><b>"+(d.t??0)+"</b>class turns<br>this week</div><div><b>"+(d.st??0)+"</b>stars<br>all time</div><div><b>"+(d.n??0)+"</b>things she<br>remembers</div></div>";
if(d.ls)h+="<div class='h'>Last class: "+e(d.ls)+"</div>";
if(d.u)h+="<div class='h'>Updated "+e(d.u)+"</div>";
document.getElementById("c").innerHTML=h}
document.getElementById("k").onclick=()=>W.openLink("APP/classroom");
document.getElementById("f").onclick=()=>W.openLink("APP/dashboard");
W.onEvent("chatDataChanged",r);r();W.ready&&W.ready();
</script>""".replace("APP", APP)


def family(uid):
    h = {"Authorization": f"Bearer {os.environ['SUPABASE_ANON_KEY']}", "x-espaluz-bot-secret": os.environ.get("ESPALUZ_BOT_SECRET", "")}
    f = requests.post(SAAS, json={"mode": "facts_get", "telegram_user_id": str(uid)}, headers=h, timeout=20).json()
    s = requests.post(SAAS, json={"mode": "stars", "telegram_user_id": str(uid)}, headers=h, timeout=20).json()
    return f, s


def state(f, s, stamp):
    p = f.get("profile") or {}
    d = {"c": str(p.get("country_now") or "").replace("_", " ").title()[:30],
         "s": STAGE.get(p.get("moved_when"), -1),
         "m": [[str(x.get("name") or "")[:20], x.get("age")] for x in (f.get("members") or [])[:6]],
         "t": int(f.get("lesson_turns") or 0), "st": int(s.get("stars") or 0), "n": len(f.get("facts") or []),
         "ls": str((f.get("lessons") or [""])[0])[:80], "u": stamp}
    out = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    while len(out.encode()) > 1024 and d["m"]:  # chat_data is at most 1024 bytes
        d["m"].pop()
        out = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    return out


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--to", required=True)
    a.add_argument("--edit", type=int)
    a.add_argument("--dry", action="store_true")
    o = a.parse_args()
    f, s = family(o.to)
    if not f.get("linked"):
        sys.exit("not linked: this Telegram user has no family on the web, nothing to show")
    from datetime import datetime, timezone
    data = state(f, s, datetime.now(timezone.utc).strftime("%d %b %H:%M UTC"))
    z = len(zlib.compress(HTML.encode(), 9))
    print(f"html {len(HTML.encode())} B, zlib {z} B (limit 4096), chat_data {len(data.encode())} B (limit 1024)")
    if z > 4096:
        sys.exit("widget too large")
    if o.dry:
        print("chat_data keys:", list(json.loads(data).keys()))
        return
    api = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}"
    if o.edit:
        r = requests.post(f"{api}/editMessageWidgetData", json={"chat_id": int(o.to), "message_id": o.edit, "chat_data": data}, timeout=20)
    else:
        r = requests.post(f"{api}/sendWidget", json={"chat_id": int(o.to), "html": HTML, "chat_data": data,
                                                     "caption": "🌴 Tu camino con EspaLuz · Your family's road"}, timeout=20)
    j = r.json()
    if j.get("ok"):
        res = j.get("result")
        print(f"🪧 family road widget {'updated' if o.edit else 'sent'}: message_id={res.get('message_id') if isinstance(res, dict) else o.edit}")
    else:
        print(f"⚠️ family road widget: HTTP {r.status_code} {j.get('description')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
