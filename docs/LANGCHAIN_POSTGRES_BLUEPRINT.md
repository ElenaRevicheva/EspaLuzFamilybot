# 🧠 EspaLuz Memory Architecture: PostgreSQL + LangChain

## Project Blueprint v1.0 - FUTURE CONSIDERATION

**Status:** 📋 BLUEPRINT ONLY - Not implemented  
**Created:** January 19, 2026  
**Purpose:** Reference document for future LangChain integration

> **Note:** This document outlines a potential future architecture combining PostgreSQL with LangChain for advanced memory management. Currently, we are focusing on pure PostgreSQL optimization. This blueprint is saved for future consideration when/if more advanced AI memory features are needed.

---

## 🎯 The Goal

Create a **unified memory system** for both Telegram and WhatsApp EspaLuz bots that:

1. **Remembers users across sessions** (not just within one conversation)
2. **Tracks learning progress** (vocabulary, mistakes, strengths)
3. **Knows each family member** (names, ages, preferences)
4. **Recognizes emotional patterns** (over weeks, not just one message)
5. **Provides proactive assistance** (tips, reminders, celebrations)
6. **Serves all 3 user types** (Expats, Travelers, Locals)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERACTION LAYER                             │
├─────────────────────────────┬───────────────────────────────────────────────┤
│      TELEGRAM BOT           │              WHATSAPP BOT                      │
│   (telebot / pyTelegramBot) │         (Twilio + Flask)                      │
└─────────────────────────────┴───────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LANGCHAIN MEMORY LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌───────────────────┐  │
│  │ ConversationMemory   │  │   EntityMemory       │  │  VectorMemory     │  │
│  │ (Recent messages)    │  │ (Names, facts, prefs)│  │ (Semantic search) │  │
│  └──────────────────────┘  └──────────────────────┘  └───────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │              PostgresChatMessageHistory                               │   │
│  │              (Persistent conversation storage)                        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI PROCESSING LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌───────────────────┐  │
│  │   Claude Sonnet 4    │  │   OpenAI Whisper     │  │  Microsoft TTS    │  │
│  │   (Conversation AI)  │  │   (Transcription)    │  │  (Neural voices)  │  │
│  └──────────────────────┘  └──────────────────────┘  └───────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      POSTGRESQL DATA LAYER (Oracle Cloud)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │  USER PROFILES  │  │ FAMILY MEMBERS  │  │    LEARNING PROGRESS        │  │
│  │  (Structured)   │  │  (Structured)   │  │    (Structured + JSON)      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ CHAT HISTORY    │  │ ENTITY STORE    │  │    VECTOR EMBEDDINGS        │  │
│  │ (LangChain)     │  │ (LangChain)     │  │    (pgvector - optional)    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ SUBSCRIPTIONS   │  │ DAILY ANALYTICS │  │    SCHEDULED TASKS          │  │
│  │ (Business)      │  │ (Investors)     │  │    (Proactive tips)         │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔗 LangChain Components for Future Use

### 1. PostgresChatMessageHistory
- Stores full conversation history in PostgreSQL
- Enables cross-session memory
- Package: `langchain-postgres`

### 2. ConversationBufferWindowMemory
- Keeps last N messages in context
- Reduces token usage

### 3. ConversationEntityMemory
- Extracts entities (names, places, facts) automatically
- Stores in structured format

### 4. ConversationSummaryBufferMemory
- Summarizes old conversations
- Keeps recent messages verbatim
- Reduces token costs for long conversations

---

## 💡 When to Consider LangChain

Consider implementing LangChain when:
- [ ] User base exceeds 1000+ active users
- [ ] Token costs become significant (>$200/month)
- [ ] Need semantic search ("What did I ask about Panama?")
- [ ] Building RAG (Retrieval Augmented Generation) features
- [ ] Want automatic entity extraction without custom code

---

## 📝 Notes

- LangChain library is **free** (open source)
- Main cost would be additional Claude API calls for summarization/entity extraction
- Can be implemented incrementally (start with chat history, add features later)
- Current pure-PostgreSQL approach handles 80% of use cases

---

**See Also:**
- `POSTGRES_UNIFIED_SCHEMA.md` - Pure PostgreSQL implementation (current focus)
- `UNIFIED_VISION_ROADMAP.md` - Overall product vision
- `SWOT_ANALYSIS_ESPALUZ.md` - Strategic analysis

---

*Document saved for future reference. Focus is currently on pure PostgreSQL optimization.*
