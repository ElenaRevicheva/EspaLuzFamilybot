# EspaLuz Current Status - June 29, 2026

## Vision Achievement: ~94%

EspaLuz is a truly emotionally intelligent AI personal assistant and bilingual Spanish-English tutor serving:
- Expats and Expat Families
- Travelers On-the-Go  
- Locals learning English

---

## Platform Status

| Platform | Status | Last Update |
|----------|--------|-------------|
| **WhatsApp** | ✅ Running | June 29 — PagueloFacil `pagar`, iron-clad access, expiry reminders |
| **Telegram** | ✅ Running | June 29 — iron-clad access fix, PF/trial expiry reminders |
| **Payment webhooks** | ✅ Running | `espaluz-payments-webhook` on Oracle :5000 |

**Oracle Server:** 170.9.242.90 (bot + webhook services active)

**Canonical repos:** [EspaLuzWhatsApp](https://github.com/ElenaRevicheva/EspaLuzWhatsApp) · [EspaLuzFamilybot](https://github.com/ElenaRevicheva/EspaLuzFamilybot)

---

## June 29, 2026 — Iron-Clad Access + Expiry Reminders (Both Platforms)

### Problem solved
Users could continue learning after trial or PagueloFacil expired. Telegram `is_subscribed()` had a 7-day grace period and defaulted to `True` — effectively no enforcement.

### Solution (WhatsApp + Telegram)

| Feature | WhatsApp | Telegram |
|---------|----------|----------|
| Access gate | `trial_system.is_user_allowed()` in `espaluz_bridge.py` | `enforce_learning_access()` → `paypal_system.is_user_allowed()` |
| Blocked message | *"Tu viaje de aprendizaje está en pausa"* | Same (bilingual) |
| Trial reminders | 2 days + 24 hours before end | Same |
| PagueloFacil reminders | 3 days + 24 hours before `paid_until` | Same |
| Reminder dedupe | Once per threshold; PF flags in `paguelofacil_payments.json` | Same |
| Still works when blocked | `pagar`, email/sub ID | `/pagar`, `/subscribe`, `/link`, `/trial`, `/help` |

### PagueloFacil WhatsApp (June 27–29)

- `espaluz_paguelofacil_wa.py` — loads live CCLW from Familybot `.env`
- `pagar` before access gate; webhook grants 30 days + WhatsApp notify
- Shared store: `paguelofacil_payments.json` with `WA:` / `TG:` keys
- Help menu includes payment section

See EspaLuzWhatsApp `docs/CURRENT_STATUS_JUNE29.md` for WhatsApp-specific detail.

---

## June 30, 2026 — Memory, RAG, LangChain & Evolving Intelligence

### Telegram evolves with the user (survives redeploy)

Every tutor reply on Telegram loads **persistent memory before the LLM call** and **writes back after**:

| Layer | Where | Telegram wiring (`main.py`) |
|-------|-------|----------------------------|
| **LangChain** | `chat_message_history` | `format_mcp_request()` — last 5 turns |
| **RAG** | `espaluz_embeddings` | `retrieve_context()` before Claude; `save_turn()` after reply |
| **Emotional IQ** | Session JSON + PG `emotional_history` | `enhanced_emotion_detection()` + `memory.track_emotion()` |
| **User facts** | `user_memories` | Onboarding + `memory.save_memory()` |
| **Rich session** | `user_sessions.json` | Learning path, emotion window, message history — reloaded on startup |

**Live proof (Elena `telegram_id=5481526862`, June 30):** 40 LangChain turns (incl. San Agustín / Alisa schools), 20 RAG embeddings, 21 emotional PG rows, 26 messages in session JSON — **unchanged after bot restart**.

### LLM resilience (`6a61a9a`)

Claude → Groq → OpenAI gpt-4o-mini → GPT-4, using **full MCP system prompt** (memory + RAG preserved). Convo-mode Groq uses `requests` (fixed urllib Cloudflare bug).

### Session UUID alignment (`289d08e`)

Same as WhatsApp: `espaluz_memory.get_session_uuid()` aligns LangChain, RAG, and SQL history.

### Safe deploy

```bash
cd /home/ubuntu/EspaLuzFamilybot
git fetch origin main
git checkout origin/main -- main.py espaluz_memory.py espaluz_rag.py
sudo systemctl restart espaluz-familybot
bash /home/ubuntu/cto-aipa/scripts/oracle-resilience/verify-espaluz-memory-persistence.sh
python3 /home/ubuntu/cto-aipa/scripts/oracle-resilience/inspect_telegram_user.py <telegram_id>
```

Runtime JSON (`user_sessions.json`, `paguelofacil_payments.json`, etc.) is **gitignored** — never overwrite from dev.

### Git / Oracle sync (June 30, 2026)

| Location | Commit | Status |
|----------|--------|--------|
| **GitHub `main`** | `289d08e` (+ `6a61a9a` LLM fallback) | Source of truth |
| **Oracle VM** | Checked out from `origin/main` | ✅ Synced, both bots active |
| **Local** | `289d08e` | ✅ Matches GitHub |

---

## June 28, 2026 - PagueloFacil Payments (Telegram)

### Why PagueloFacil
PagueloFacil does not support recurring subscriptions. Telegram now offers a one-time **$11 / 30 days** checkout for Panama and LATAM users who prefer local card payment over PayPal.

### Two payment paths

| Path | Command | After payment | Billing |
|------|---------|---------------|---------|
| **PagueloFacil** | `/pagar` or `/pay` | Automatic — webhook grants access | One-time $11 / 30 days |
| **PayPal** | `/subscribe` then `/link` | User sends `I-XXXX…` or PayPal email | Recurring subscription |

### Architecture

```
/pagar  →  LinkDeamon.cfm (PARM_1=telegram_id)  →  PagueloFacil checkout
PagueloFacil  →  POST https://webhook.aideazz.xyz/paguelofacil-webhook
             →  paypal_webhook_server.py (:5000)
             →  paguelofacil_payments.json + Telegram confirmation
```

- **Merchant:** `aideazz` (CCLW in Oracle `.env`, not in git)
- **Webhook URL:** registered with PagueloFacil support, June 2026
- **Access store:** `paguelofacil_payments.json` (not yet synced to PostgreSQL `subscriptions`)

### Key files

| File | Role |
|------|------|
| `espaluz_paguelofacil.py` | Checkout links, webhook processing, access grants |
| `paypal_webhook_server.py` | `/paguelofacil-webhook`, `/paypal-webhook`, `/health` |
| `main.py` | `/pagar`, `/pay`; subscription checks include PF access |
| `espaluz_paypal_system.py` | Unified subscription check |
| `deploy/espaluz-payments-webhook.service` | systemd unit (venv Python) |
| `deploy/grant_manual_pf_payment.py` | Manual grant if webhook missed |
| `deploy/ORACLE_SHELL.txt` | Deploy and verification commands |

### Production fix (June 28)
First live payment webhook arrived with `authStatus: "00"` but was skipped due to strict JSON parse on large payloads and missing `authStatus` check. Fixed in `686a5e4` (tolerant parse + accept `authStatus: "00"`).

**Status:** LIVE — see also `docs/SWOT_ANALYSIS_ESPALUZ.md` → **💳 PAGUELOFACIL PAYMENTS**

---

## January 25, 2026 - Bug Fixes Applied

### WhatsApp Fix
- **Bug:** `name 'message_text' is not defined` in voice handler
- **Root Cause:** Lines 3181, 3186 used `message_text` which was not in scope
- **Fix:** Changed to `spanish_input` (the correct variable)
- **Status:** FIXED and deployed

### Telegram Enhancement  
- **Feature:** PostgreSQL `family_members` table integration
- **Added:** `add_family()` helper method in `espaluz_memory.py`
- **Updated:** `main.py` now saves family data to BOTH:
  - `user_memories` table (backward compatible)
  - `family_members` table (proper relational storage)
- **Status:** IMPLEMENTED and deployed

---

## Database Status (espaluz_unified) — June 30, 2026

| Table | Records | Status |
|-------|---------|--------|
| users | 19 | Working |
| chat_message_history | 344 | LangChain + legacy rows |
| espaluz_embeddings | 82 | RAG semantic memory (pgvector) |
| emotional_history | 133 | Working |
| vocabulary | 75 | Working |
| user_memories | 13 | Working |
| subscriptions | 12 | PayPal; PF access in JSON for now |
| family_members | 0+ | Ready (onboarding writes here) |

**LangChain:** `LANGCHAIN_AVAILABLE = True` on Oracle  
**RAG:** Requires `OPENAI_API_KEY` + `espaluz_embeddings` table (migration in WhatsApp `config/migrations/001_espaluz_embeddings.sql`)

Per-user inspect: `python3 /home/ubuntu/cto-aipa/scripts/oracle-resilience/inspect_telegram_user.py <telegram_id>`

---

## Working Features (Both Bots)

### Core Learning
- Bilingual responses (Spanish-English)
- Russian to Spanish + English dual translation
- Voice messages with Neural TTS (edge-tts)
- Photo/image OCR translation
- Pronunciation guides [like-THIS] (text only, not spoken)

### 21 Spanish-Speaking Countries
- All 21 countries recognized
- Local slang WITH meanings
- Cultural tips
- Emergency numbers
- Currency and timezone info

### Practical Help Commands
- help banking
- help medical
- help school
- help shopping
- help transport
- help emergency
- help housing
- help immigration

### Emotional Intelligence
- Mood detection (50+ emotional states)
- Emotional history tracked to PostgreSQL
- Adaptive responses
- Family member awareness

### Family Memory (Enhanced Jan 25)
- Remembers names
- Family members stored in PostgreSQL (new!)
- Ages, relationships tracked
- Onboarding flow with DB sync
- Cross-session persistence via LangChain

### PostgreSQL + LangChain + RAG Integration
- Unified `espaluz_unified` database
- LangChain chat history — **read into prompt** (last 5 turns) + write after each reply
- RAG pgvector — semantic recall of past topics (schools, family, relocation)
- Emotional history to PostgreSQL + session JSON for in-conversation mood
- Vocabulary tracking with SM-2 algorithm
- **Note:** WhatsApp and Telegram sessions are separate UUIDs per platform (not auto-merged)

### Payments (Telegram — June 2026)
- PagueloFacil `/pagar` — automatic 30-day access via webhook
- PayPal `/subscribe` + `/link` — recurring subscriptions
- 14-day free trial (`/trial`)
- Menu/help explain both payment paths

---

## WhatsApp Exclusive Features

### Translate Mode
- "translate mode" trigger
- Neural voice replies
- Russian to Both ES + EN

### Business English (4 Modules)
- Customer Service
- Hotel/Hospitality
- Retail/Sales
- Phone/Email

### Housing/Apartments
- Popular areas by country
- Average rent prices
- Search websites
- Key phrases

### Learning Preferences
- Pace (slow/moderate/fast)
- Style (auditory/visual)
- Correction style
- Focus areas

### Proactive Follow-ups
- Doctor appointments (24h)
- Job interviews (48h)
- Moving (72h)
- School enrollment (1 week)

### Enhanced Responses
- 10-15 natural emojis per response
- Country flags
- Section headers with emojis
- Warm, engaging tone

---

## Complete WhatsApp Menu

```
TUTOR MODE (Default)
TRANSLATE MODE
MOTIVATIONAL MODE
PRACTICAL HELP (7 topics)
RELOCATION HELP
BUSINESS ENGLISH (4 modules)
PERSONALIZATION
```

---

## Technical Stack

- **Runtime**: Python 3.11+
- **Database**: PostgreSQL (Oracle Cloud) - `espaluz_unified`
- **Memory**: LangChain PostgresChatMessageHistory
- **TTS**: edge-tts (Microsoft Neural Voices)
- **AI**: Claude API (Anthropic)
- **Hosting**: Oracle Cloud Infrastructure (`170.9.242.90`)
- **WhatsApp**: Twilio API
- **Telegram**: python-telegram-bot
- **Payments**: PagueloFacil one-time (`/pagar`) + PayPal subscriptions (`/subscribe`, `/link`)
- **Webhooks**: Flask `paypal_webhook_server.py` → `https://webhook.aideazz.xyz/`

---

## Key Files

### WhatsApp
- `espaluz_bridge.py` - Main bot (~320KB)
- `espaluz_memory.py` - Unified memory system (shared)
- `espaluz_advanced_features.py` - Housing, Business English, Preferences
- `espaluz_country_contexts_full.py` - 21 countries deep data
- `whatsapp_convo_mode.py` - Translate mode
- `whatsapp_practical_help.py` - Help commands

### Telegram
- `main.py` - Main bot (~219KB)
- `espaluz_memory.py` - Unified memory system (shared)
- `espaluz_country_contexts.py` - Country data
- `espaluz_emotional_brain.py` - Emotional intelligence
- `espaluz_enhancements.py` - 21 countries, 8 features
- `espaluz_paguelofacil.py` - PagueloFacil checkout + webhook processing
- `espaluz_paypal_system.py` - PayPal + unified subscription checks
- `paypal_webhook_server.py` - Payment webhooks (PayPal + PagueloFacil)

---

## Backup Branches

| Branch | Description |
|--------|-------------|
| `backup-jan25-before-fixes` | Both repos - before Jan 25 fixes |
| `backup-final-jan24-complete` | Full WhatsApp with all features |
| `backup-full-vision-jan24` | Before emoji enhancement |
| `backup-with-practical-help-jan24` | After practical help |
| `backup-complete-with-russian-jan24` | After Russian translation |

---

## Verified Working (June 26)

- PostgreSQL connection: `Database URL found`
- Tables initialized successfully
- LangChain: `LANGCHAIN_AVAILABLE = True`
- Both bot services: `active` on Oracle
- Payment webhook: `espaluz-payments-webhook` active on `:5000`
- PagueloFacil: `/pagar` checkout + webhook auto-grant (post `686a5e4` fix)
- PayPal: `/subscribe` + manual `/link` still working

---

## Known Issues Resolved

| Issue | Status | Date Fixed |
|-------|--------|------------|
| `message_text` undefined error | FIXED | Jan 25, 2026 |
| Family members not in DB | FIXED | Jan 25, 2026 |
| PagueloFacil webhook skipped (`authStatus 00`) | FIXED | Jun 28, 2026 |
| Webhook service crash (systemd python path) | FIXED | Jun 2026 |
| Enhancement slice error | Exists (non-fatal) | - |

---

## Next Steps (Future)

1. Sync PagueloFacil access to PostgreSQL `subscriptions` table
2. Port `/pagar` to WhatsApp (reuse `espaluz_paguelofacil.py`)
3. Port Business English to Telegram
4. Port Housing module to Telegram
5. Build Investor Dashboard (Phase 7)
6. Proactive tip scheduler
7. Real apartment listings API

---

*Last updated: June 26, 2026*
