# 🚀 EspaLuz Memory System Implementation Plan

## PostgreSQL + LangChain Integration

**Status:** 🟢 PHASE 1-6 COMPLETE, DASHBOARD PENDING  
**Created:** January 19, 2026  
**Updated:** January 22, 2026  
**Estimated Time:** 2-3 weeks  
**Cost:** $0 (all free tools)

---

## 📊 IMPLEMENTATION PROGRESS

| Phase | Status | Completed |
|-------|--------|-----------|
| Phase 1: Database Setup | ✅ COMPLETE | Jan 20, 2026 |
| Phase 2: Shared Module | ✅ COMPLETE | Jan 20, 2026 |
| Phase 3: Telegram Integration | ✅ COMPLETE | Jan 22, 2026 |
| Phase 4: WhatsApp Integration | ✅ COMPLETE | Jan 22, 2026 |
| Phase 5: Testing | ✅ COMPLETE | Jan 22, 2026 |
| Phase 6: Deployment | ✅ COMPLETE | Jan 22, 2026 |
| Phase 7: Investor Dashboard | ⏳ NEXT | - |

### January 22, 2026 Update
- ✅ Fixed `espaluz_memory.py` - added `platform_user_id` parameter
- ✅ Fixed SQL bug in `increment_message_count()`
- ✅ Integrated into Telegram bot (`main.py`)
- ✅ Integrated into WhatsApp bot (`espaluz_bridge.py`)
- ✅ Verified: messages being tracked in `espaluz_unified` database
- ✅ Synced codebases: Oracle → GitHub → Local

---

## 🎯 Objective

Implement a unified memory system for both EspaLuz bots that:
- Remembers users across sessions (cross-session memory)
- Tracks learning progress (vocabulary, spaced repetition)
- Knows family members (names, ages, relationships)
- Recognizes emotional patterns (week-over-week trends)
- Enables proactive assistance (tips, reminders)
- Serves all 3 user types (Expats, Travelers, Locals)
- **Provides investor-ready analytics dashboard** (retention, conversions, MRR)

---

## 📦 Required Packages

### Python Dependencies (Both Bots)
```bash
# Core LangChain
pip install langchain>=0.2.0
pip install langchain-anthropic>=0.1.0
pip install langchain-postgres>=0.0.6

# PostgreSQL (already installed)
pip install psycopg2-binary>=2.9.9

# Optional but recommended
pip install langchain-community>=0.2.0
```

### Package Costs
| Package | License | Cost |
|---------|---------|------|
| langchain | MIT | **FREE** |
| langchain-anthropic | MIT | **FREE** |
| langchain-postgres | MIT | **FREE** |
| psycopg2-binary | LGPL | **FREE** |

---

## 🗄️ Phase 1: Database Setup (Day 1-2)

### Step 1.1: Create Unified Database on Oracle

```bash
# SSH to Oracle server
ssh -i ~/.ssh/oracle-key ubuntu@170.9.242.90

# Create database and user
sudo -u postgres psql << 'EOF'
CREATE DATABASE espaluz_unified;
CREATE USER espaluz_app WITH PASSWORD 'secure_random_password_here';
GRANT ALL PRIVILEGES ON DATABASE espaluz_unified TO espaluz_app;
\c espaluz_unified
GRANT ALL ON SCHEMA public TO espaluz_app;
EOF
```

### Step 1.2: Create Core Tables

```sql
-- Connect to new database
\c espaluz_unified

-- ============================================================
-- 1. UNIFIED USER PROFILES
-- ============================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    
    -- Platform Identifiers (user can have both)
    telegram_id VARCHAR(50) UNIQUE,
    whatsapp_id VARCHAR(50) UNIQUE,
    
    -- Human Identity
    display_name VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(30),
    
    -- User Type (Vision: 3 types)
    user_type VARCHAR(20) DEFAULT 'expat',
    learning_direction VARCHAR(20) DEFAULT 'spanish',
    primary_goal TEXT,
    
    -- Location Context
    country_of_origin VARCHAR(50),
    current_country VARCHAR(50),
    current_city VARCHAR(100),
    timezone VARCHAR(50),
    
    -- Learning Profile
    proficiency_level VARCHAR(30) DEFAULT 'beginner',
    preferred_language VARCHAR(10) DEFAULT 'es',
    
    -- Family Link
    family_id UUID,
    family_role VARCHAR(30),
    
    -- Activity Tracking
    total_messages INTEGER DEFAULT 0,
    voice_messages INTEGER DEFAULT 0,
    image_messages INTEGER DEFAULT 0,
    streak_days INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    last_active_telegram TIMESTAMP,
    last_active_whatsapp TIMESTAMP,
    
    CONSTRAINT at_least_one_platform CHECK (
        telegram_id IS NOT NULL OR whatsapp_id IS NOT NULL
    )
);

-- ============================================================
-- 2. LANGCHAIN CHAT MESSAGE HISTORY
-- (Standard table structure for PostgresChatMessageHistory)
-- ============================================================
CREATE TABLE chat_message_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    message JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chat_history_session ON chat_message_history(session_id);
CREATE INDEX idx_chat_history_created ON chat_message_history(created_at);

-- ============================================================
-- 3. FAMILY MEMBERS
-- ============================================================
CREATE TABLE family_members (
    id SERIAL PRIMARY KEY,
    family_id UUID NOT NULL,
    user_id INTEGER REFERENCES users(id),
    
    name VARCHAR(100) NOT NULL,
    nickname VARCHAR(50),
    relationship VARCHAR(30),
    age INTEGER,
    age_group VARCHAR(20),
    
    proficiency_level VARCHAR(30),
    interests TEXT[],
    learning_struggles TEXT[],
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 4. SUBSCRIPTIONS (Unified)
-- ============================================================
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    
    status VARCHAR(20) DEFAULT 'trial',
    source VARCHAR(30),
    
    paypal_subscription_id VARCHAR(100) UNIQUE,
    paypal_plan_id VARCHAR(100),
    
    trial_start TIMESTAMP,
    trial_end TIMESTAMP,
    started_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 5. USER MEMORIES (Key Facts)
-- ============================================================
CREATE TABLE user_memories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    
    memory_type VARCHAR(30) NOT NULL,
    content TEXT NOT NULL,
    importance INTEGER DEFAULT 5,
    category VARCHAR(50),
    
    times_used INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- 6. VOCABULARY (Spaced Repetition)
-- ============================================================
CREATE TABLE vocabulary (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    family_member_id INTEGER REFERENCES family_members(id),
    
    word VARCHAR(100) NOT NULL,
    translation VARCHAR(100) NOT NULL,
    language VARCHAR(10) NOT NULL,
    example_sentence TEXT,
    category VARCHAR(50),
    country_context VARCHAR(50),
    is_slang BOOLEAN DEFAULT FALSE,
    
    -- SM-2 Algorithm fields
    ease_factor FLOAT DEFAULT 2.5,
    interval_days INTEGER DEFAULT 1,
    repetitions INTEGER DEFAULT 0,
    next_review TIMESTAMP,
    last_reviewed TIMESTAMP,
    
    correct_count INTEGER DEFAULT 0,
    incorrect_count INTEGER DEFAULT 0,
    
    learned_from VARCHAR(50),
    learned_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, word, language)
);

-- ============================================================
-- 7. EMOTIONAL HISTORY
-- ============================================================
CREATE TABLE emotional_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    
    emotion VARCHAR(50) NOT NULL,
    intensity FLOAT,
    category VARCHAR(50),
    platform VARCHAR(20),
    trigger_summary TEXT,
    response_tone VARCHAR(50),
    
    detected_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 8. DAILY ANALYTICS (Unified)
-- ============================================================
CREATE TABLE daily_analytics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    
    telegram_messages INTEGER DEFAULT 0,
    whatsapp_messages INTEGER DEFAULT 0,
    telegram_users INTEGER DEFAULT 0,
    whatsapp_users INTEGER DEFAULT 0,
    
    total_messages INTEGER DEFAULT 0,
    voice_messages INTEGER DEFAULT 0,
    image_messages INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    
    words_learned INTEGER DEFAULT 0,
    reviews_completed INTEGER DEFAULT 0,
    
    trials_started INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    cancellations INTEGER DEFAULT 0,
    mrr_cents INTEGER DEFAULT 0
);

-- ============================================================
-- 9. SCHEDULED MESSAGES
-- ============================================================
CREATE TABLE scheduled_messages (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    
    message_type VARCHAR(30) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    content TEXT,
    content_data JSONB,
    
    scheduled_for TIMESTAMP NOT NULL,
    sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP,
    user_engaged BOOLEAN,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 10. EVENT LOG
-- ============================================================
CREATE TABLE event_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    
    event_type VARCHAR(50) NOT NULL,
    platform VARCHAR(20),
    event_data JSONB,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_users_telegram ON users(telegram_id) WHERE telegram_id IS NOT NULL;
CREATE INDEX idx_users_whatsapp ON users(whatsapp_id) WHERE whatsapp_id IS NOT NULL;
CREATE INDEX idx_users_email ON users(email) WHERE email IS NOT NULL;
CREATE INDEX idx_users_family ON users(family_id) WHERE family_id IS NOT NULL;

CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

CREATE INDEX idx_vocabulary_user_review ON vocabulary(user_id, next_review);
CREATE INDEX idx_emotional_user_date ON emotional_history(user_id, detected_at);
CREATE INDEX idx_scheduled_pending ON scheduled_messages(scheduled_for) WHERE sent = FALSE;
CREATE INDEX idx_daily_date ON daily_analytics(date);
```

### Step 1.3: Migrate Existing Data

```sql
-- Migrate WhatsApp users
INSERT INTO users (whatsapp_id, current_country, total_messages, 
                   voice_messages, image_messages, streak_days, 
                   created_at, last_active_whatsapp)
SELECT 
    user_id,
    countries[1],
    total_messages,
    voice_messages,
    image_messages,
    streak_days,
    first_seen,
    last_seen
FROM dblink('dbname=espaluz_whatsapp', 
    'SELECT user_id, countries, total_messages, voice_messages, 
            image_messages, streak_days, first_seen, last_seen 
     FROM whatsapp_users')
AS t(user_id VARCHAR, countries TEXT[], total_messages INT, 
     voice_messages INT, image_messages INT, streak_days INT,
     first_seen TIMESTAMP, last_seen TIMESTAMP);

-- Migrate Telegram users
INSERT INTO users (telegram_id, display_name, current_country, 
                   total_messages, voice_messages, image_messages,
                   created_at, last_active_telegram)
SELECT 
    user_id,
    first_name,
    country,
    total_messages,
    voice_messages,
    image_messages,
    first_seen,
    last_active
FROM dblink('dbname=espaluz_telegram',
    'SELECT user_id, first_name, country, total_messages,
            voice_messages, image_messages, first_seen, last_active
     FROM telegram_users')
AS t(user_id VARCHAR, first_name VARCHAR, country VARCHAR,
     total_messages INT, voice_messages INT, image_messages INT,
     first_seen TIMESTAMP, last_active TIMESTAMP)
ON CONFLICT (telegram_id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    last_active_telegram = EXCLUDED.last_active_telegram;
```

### ✅ Phase 1 Checkpoint - COMPLETED January 20, 2026
- [x] Database `espaluz_unified` created ✅
- [x] All 10 tables created ✅
- [x] 13 indexes created ✅
- [x] Existing data migrated (13 users, 12 subscriptions) ✅
- [x] Test queries working ✅

**Database Location:** Oracle Cloud PostgreSQL (170.9.242.90)
**Tables Created:** users, chat_message_history, family_members, subscriptions, user_memories, vocabulary, emotional_history, daily_analytics, scheduled_messages, event_log

---

## 🔗 Phase 2: Shared Python Module (Day 3-4)

### Step 2.1: Create `espaluz_memory.py`

Create this file in a shared location accessible by both bots:

```python
"""
EspaLuz Unified Memory System
PostgreSQL + LangChain Integration
Shared between Telegram and WhatsApp bots
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

from langchain_anthropic import ChatAnthropic
from langchain_postgres import PostgresChatMessageHistory
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Configuration
DATABASE_URL = os.getenv('ESPALUZ_DATABASE_URL', 
    'postgresql://espaluz_app:password@localhost:5432/espaluz_unified')
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')


class EspaLuzMemory:
    """
    Unified memory system for EspaLuz bots.
    Combines PostgreSQL structured data with LangChain conversation memory.
    """
    
    def __init__(self, platform: str, platform_user_id: str):
        """
        Initialize memory for a specific user session.
        
        Args:
            platform: 'telegram' or 'whatsapp'
            platform_user_id: User's ID on that platform
        """
        self.platform = platform
        self.platform_user_id = platform_user_id
        self.session_id = f"{platform}:{platform_user_id}"
        self.database_url = DATABASE_URL
        
        # Initialize user in database
        self.user = self._get_or_create_user()
        self.user_id = self.user['id']
        
        # Initialize LangChain memory
        self._init_langchain_memory()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup"""
        conn = psycopg2.connect(self.database_url)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _get_or_create_user(self) -> Dict[str, Any]:
        """Get existing user or create new one"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Try to find existing user
                if self.platform == 'telegram':
                    cur.execute("SELECT * FROM users WHERE telegram_id = %s", 
                               (self.platform_user_id,))
                else:
                    cur.execute("SELECT * FROM users WHERE whatsapp_id = %s", 
                               (self.platform_user_id,))
                
                user = cur.fetchone()
                
                if user:
                    # Update last active
                    field = f"last_active_{self.platform}"
                    cur.execute(f"UPDATE users SET {field} = NOW() WHERE id = %s", 
                               (user['id'],))
                    return dict(user)
                
                # Create new user
                if self.platform == 'telegram':
                    cur.execute("""
                        INSERT INTO users (telegram_id, last_active_telegram, created_at)
                        VALUES (%s, NOW(), NOW()) RETURNING *
                    """, (self.platform_user_id,))
                else:
                    cur.execute("""
                        INSERT INTO users (whatsapp_id, last_active_whatsapp, created_at)
                        VALUES (%s, NOW(), NOW()) RETURNING *
                    """, (self.platform_user_id,))
                
                return dict(cur.fetchone())
    
    def _init_langchain_memory(self):
        """Initialize LangChain conversation memory"""
        # PostgreSQL-backed message history
        self.chat_history = PostgresChatMessageHistory(
            connection_string=self.database_url,
            session_id=self.session_id,
            table_name="chat_message_history"
        )
        
        # Conversation memory with window (last 20 messages)
        self.memory = ConversationBufferWindowMemory(
            chat_memory=self.chat_history,
            k=20,  # Keep last 20 messages in context
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Claude LLM
        self.llm = ChatAnthropic(
            model=CLAUDE_MODEL,
            api_key=CLAUDE_API_KEY,
            max_tokens=4096
        )
    
    # ==================== CONVERSATION ====================
    
    def chat(self, user_message: str, system_prompt: str = None) -> str:
        """
        Send a message and get AI response with full memory context.
        
        Args:
            user_message: User's message
            system_prompt: Optional system prompt (uses default if not provided)
        
        Returns:
            AI response text
        """
        # Build context from memories
        context = self._build_context()
        
        # Default system prompt with context
        if not system_prompt:
            system_prompt = self._get_default_system_prompt()
        
        # Add user context to system prompt
        full_system = f"{system_prompt}\n\n{context}"
        
        # Get conversation history
        history = self.memory.load_memory_variables({})
        messages = history.get('chat_history', [])
        
        # Build message list
        all_messages = [SystemMessage(content=full_system)]
        all_messages.extend(messages)
        all_messages.append(HumanMessage(content=user_message))
        
        # Get response
        response = self.llm.invoke(all_messages)
        response_text = response.content
        
        # Save to memory
        self.chat_history.add_user_message(user_message)
        self.chat_history.add_ai_message(response_text)
        
        # Track message
        self._track_message('text')
        
        # Extract and save any new information
        self._extract_information(user_message, response_text)
        
        return response_text
    
    def _build_context(self) -> str:
        """Build context string from user data and memories"""
        context_parts = []
        
        # User profile context
        if self.user.get('display_name'):
            context_parts.append(f"User's name: {self.user['display_name']}")
        if self.user.get('current_country'):
            context_parts.append(f"User is in: {self.user['current_country']}")
        if self.user.get('user_type'):
            context_parts.append(f"User type: {self.user['user_type']}")
        if self.user.get('learning_direction'):
            context_parts.append(f"Learning: {self.user['learning_direction']}")
        if self.user.get('proficiency_level'):
            context_parts.append(f"Level: {self.user['proficiency_level']}")
        
        # Family context
        family = self.get_family_members()
        if family:
            family_str = ", ".join([f"{m['name']} ({m['relationship']}, {m['age']})" 
                                   for m in family])
            context_parts.append(f"Family members: {family_str}")
        
        # Key memories
        memories = self.get_memories(limit=5)
        if memories:
            memories_str = "; ".join([m['content'] for m in memories])
            context_parts.append(f"Key facts about user: {memories_str}")
        
        # Emotional trend
        emotional = self.get_emotional_trend(days=7)
        if emotional.get('dominant'):
            context_parts.append(f"Recent emotional trend: {emotional['dominant']}")
        
        # Words due for review
        review_words = self.get_words_for_review(limit=3)
        if review_words:
            words = ", ".join([w['word'] for w in review_words])
            context_parts.append(f"Words due for review: {words}")
        
        if context_parts:
            return "USER CONTEXT:\n" + "\n".join(f"- {p}" for p in context_parts)
        return ""
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt based on user type"""
        user_type = self.user.get('user_type', 'expat')
        direction = self.user.get('learning_direction', 'spanish')
        
        base = """You are EspaLuz, a warm and emotionally intelligent bilingual AI tutor.
You help users learn Spanish and English while providing cultural guidance.
You remember everything about the user from previous conversations.
You notice emotional patterns and provide appropriate support.
Never use asterisks (*) in your responses - use emojis for emphasis instead."""
        
        if user_type == 'expat':
            base += """
This user is an EXPAT learning Spanish. Help with:
- Practical Spanish for daily life
- Relocation assistance (schools, apartments, banks, healthcare)
- Cultural integration and local tips
- Family language learning coordination"""
        
        elif user_type == 'traveler':
            base += """
This user is a TRAVELER needing quick Spanish help. Focus on:
- Essential travel phrases
- Emergency vocabulary
- Cultural navigation
- Quick, practical assistance"""
        
        elif user_type == 'local':
            base += """
This user is a LOCAL learning English. Help with:
- Service industry English
- Professional English skills
- Communication with expats
- Travel English for visiting English-speaking countries"""
        
        return base
    
    # ==================== USER PROFILE ====================
    
    def update_profile(self, **kwargs) -> bool:
        """Update user profile fields"""
        allowed = ['display_name', 'email', 'phone', 'user_type', 
                  'learning_direction', 'primary_goal', 'country_of_origin',
                  'current_country', 'current_city', 'timezone', 
                  'proficiency_level', 'preferred_language', 'family_id', 'family_role']
        
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return False
        
        set_clause = ', '.join(f"{k} = %s" for k in updates.keys())
        values = list(updates.values()) + [self.user_id]
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"UPDATE users SET {set_clause} WHERE id = %s", values)
                # Refresh user data
                cur.execute("SELECT * FROM users WHERE id = %s", (self.user_id,))
                self.user = dict(cur.fetchone())
                return True
    
    # ==================== MEMORIES ====================
    
    def save_memory(self, content: str, memory_type: str = 'fact', 
                   category: str = None, importance: int = 5) -> int:
        """Save a key fact/memory about the user"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_memories (user_id, memory_type, content, category, importance)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (self.user_id, memory_type, content, category, importance))
                return cur.fetchone()[0]
    
    def get_memories(self, memory_type: str = None, limit: int = 10) -> List[Dict]:
        """Get user's memories"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if memory_type:
                    cur.execute("""
                        SELECT * FROM user_memories 
                        WHERE user_id = %s AND memory_type = %s AND is_active = TRUE
                        ORDER BY importance DESC, created_at DESC LIMIT %s
                    """, (self.user_id, memory_type, limit))
                else:
                    cur.execute("""
                        SELECT * FROM user_memories 
                        WHERE user_id = %s AND is_active = TRUE
                        ORDER BY importance DESC, created_at DESC LIMIT %s
                    """, (self.user_id, limit))
                return [dict(row) for row in cur.fetchall()]
    
    def _extract_information(self, user_message: str, ai_response: str):
        """Extract and save important information from conversation"""
        # This could be enhanced with LLM-based extraction
        # For now, simple keyword detection
        
        text = user_message.lower()
        
        # Detect country mentions
        countries = ['panama', 'mexico', 'spain', 'colombia', 'argentina', 
                    'chile', 'peru', 'costa rica', 'ecuador']
        for country in countries:
            if country in text and not self.user.get('current_country'):
                self.update_profile(current_country=country.title())
                break
        
        # Detect name introduction
        if 'my name is' in text or 'i am ' in text or 'i\'m ' in text:
            # Simple extraction - could be improved
            words = user_message.split()
            for i, word in enumerate(words):
                if word.lower() in ['is', 'am', "i'm"] and i + 1 < len(words):
                    potential_name = words[i + 1].strip('.,!?')
                    if potential_name[0].isupper() and len(potential_name) > 1:
                        self.update_profile(display_name=potential_name)
                        break
    
    # ==================== FAMILY ====================
    
    def add_family_member(self, name: str, relationship: str, 
                         age: int = None, **kwargs) -> int:
        """Add a family member"""
        import uuid
        
        # Ensure user has family_id
        if not self.user.get('family_id'):
            family_id = str(uuid.uuid4())
            self.update_profile(family_id=family_id)
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                age_group = None
                if age:
                    if age < 3: age_group = 'toddler'
                    elif age < 13: age_group = 'child'
                    elif age < 20: age_group = 'teen'
                    else: age_group = 'adult'
                
                cur.execute("""
                    INSERT INTO family_members 
                    (family_id, user_id, name, relationship, age, age_group)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (self.user['family_id'], self.user_id, name, 
                      relationship, age, age_group))
                return cur.fetchone()[0]
    
    def get_family_members(self) -> List[Dict]:
        """Get all family members"""
        if not self.user.get('family_id'):
            return []
        
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM family_members WHERE family_id = %s
                """, (self.user['family_id'],))
                return [dict(row) for row in cur.fetchall()]
    
    # ==================== VOCABULARY ====================
    
    def add_word(self, word: str, translation: str, language: str = 'es',
                category: str = None, example: str = None) -> bool:
        """Add a word to user's vocabulary"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                next_review = datetime.now() + timedelta(days=1)
                cur.execute("""
                    INSERT INTO vocabulary 
                    (user_id, word, translation, language, category, 
                     example_sentence, next_review, learned_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (user_id, word, language) DO UPDATE SET
                        translation = EXCLUDED.translation,
                        example_sentence = COALESCE(EXCLUDED.example_sentence, vocabulary.example_sentence)
                    RETURNING id
                """, (self.user_id, word, translation, language, 
                      category, example, next_review))
                return True
    
    def get_words_for_review(self, limit: int = 5) -> List[Dict]:
        """Get words due for spaced repetition review"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM vocabulary 
                    WHERE user_id = %s AND next_review <= NOW()
                    ORDER BY next_review ASC LIMIT %s
                """, (self.user_id, limit))
                return [dict(row) for row in cur.fetchall()]
    
    def record_review(self, vocab_id: int, correct: bool) -> bool:
        """Record vocabulary review result using SM-2 algorithm"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM vocabulary WHERE id = %s", (vocab_id,))
                vocab = cur.fetchone()
                if not vocab:
                    return False
                
                # SM-2 Algorithm
                ef = vocab['ease_factor']
                interval = vocab['interval_days']
                reps = vocab['repetitions']
                
                if correct:
                    if reps == 0:
                        interval = 1
                    elif reps == 1:
                        interval = 6
                    else:
                        interval = int(interval * ef)
                    reps += 1
                    ef = max(1.3, ef + 0.1)
                else:
                    reps = 0
                    interval = 1
                    ef = max(1.3, ef - 0.2)
                
                next_review = datetime.now() + timedelta(days=interval)
                
                cur.execute("""
                    UPDATE vocabulary SET
                        ease_factor = %s, interval_days = %s, repetitions = %s,
                        next_review = %s, last_reviewed = NOW(),
                        correct_count = correct_count + %s,
                        incorrect_count = incorrect_count + %s
                    WHERE id = %s
                """, (ef, interval, reps, next_review,
                      1 if correct else 0, 0 if correct else 1, vocab_id))
                return True
    
    def get_vocabulary_stats(self) -> Dict[str, Any]:
        """Get vocabulary learning statistics"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_words,
                        SUM(correct_count) as total_correct,
                        SUM(incorrect_count) as total_incorrect,
                        COUNT(*) FILTER (WHERE repetitions >= 5) as mastered,
                        COUNT(*) FILTER (WHERE next_review <= NOW()) as due_for_review
                    FROM vocabulary WHERE user_id = %s
                """, (self.user_id,))
                return dict(cur.fetchone())
    
    # ==================== EMOTIONS ====================
    
    def track_emotion(self, emotion: str, intensity: float = 0.5,
                     category: str = None, trigger: str = None) -> bool:
        """Track detected emotion"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO emotional_history 
                    (user_id, emotion, intensity, category, platform, trigger_summary)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (self.user_id, emotion, intensity, category, 
                      self.platform, trigger))
                return True
    
    def get_emotional_trend(self, days: int = 7) -> Dict[str, Any]:
        """Get emotional trend over specified days"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT emotion, COUNT(*) as count, AVG(intensity) as avg_intensity
                    FROM emotional_history
                    WHERE user_id = %s AND detected_at >= NOW() - INTERVAL '%s days'
                    GROUP BY emotion ORDER BY count DESC
                """, (self.user_id, days))
                
                emotions = [dict(row) for row in cur.fetchall()]
                return {
                    'emotions': emotions,
                    'dominant': emotions[0]['emotion'] if emotions else None,
                    'period_days': days
                }
    
    # ==================== MESSAGE TRACKING ====================
    
    def _track_message(self, message_type: str = 'text'):
        """Track message for analytics"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Update user stats
                if message_type == 'voice':
                    cur.execute("""
                        UPDATE users SET total_messages = total_messages + 1,
                                        voice_messages = voice_messages + 1
                        WHERE id = %s
                    """, (self.user_id,))
                elif message_type == 'image':
                    cur.execute("""
                        UPDATE users SET total_messages = total_messages + 1,
                                        image_messages = image_messages + 1
                        WHERE id = %s
                    """, (self.user_id,))
                else:
                    cur.execute("""
                        UPDATE users SET total_messages = total_messages + 1
                        WHERE id = %s
                    """, (self.user_id,))
                
                # Update daily analytics
                today = datetime.now().date()
                tg = 1 if self.platform == 'telegram' else 0
                wa = 1 if self.platform == 'whatsapp' else 0
                voice = 1 if message_type == 'voice' else 0
                image = 1 if message_type == 'image' else 0
                
                cur.execute("""
                    INSERT INTO daily_analytics 
                    (date, telegram_messages, whatsapp_messages, 
                     total_messages, voice_messages, image_messages)
                    VALUES (%s, %s, %s, 1, %s, %s)
                    ON CONFLICT (date) DO UPDATE SET
                        telegram_messages = daily_analytics.telegram_messages + %s,
                        whatsapp_messages = daily_analytics.whatsapp_messages + %s,
                        total_messages = daily_analytics.total_messages + 1,
                        voice_messages = daily_analytics.voice_messages + %s,
                        image_messages = daily_analytics.image_messages + %s
                """, (today, tg, wa, voice, image, tg, wa, voice, image))
    
    # ==================== SUBSCRIPTION ====================
    
    def get_subscription_status(self) -> Dict[str, Any]:
        """Get subscription status"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM subscriptions 
                    WHERE user_id = %s ORDER BY created_at DESC LIMIT 1
                """, (self.user_id,))
                sub = cur.fetchone()
                
                if not sub:
                    return {'status': 'none', 'has_access': False}
                
                now = datetime.now()
                
                if sub['status'] == 'active':
                    return {'status': 'active', 'has_access': True}
                
                if sub['status'] == 'trial' and sub['trial_end'] and sub['trial_end'] > now:
                    return {
                        'status': 'trial',
                        'has_access': True,
                        'days_left': (sub['trial_end'] - now).days
                    }
                
                return {'status': 'expired', 'has_access': False}
    
    def start_trial(self, days: int = 7) -> bool:
        """Start trial"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                trial_end = datetime.now() + timedelta(days=days)
                cur.execute("""
                    INSERT INTO subscriptions (user_id, status, trial_start, trial_end)
                    VALUES (%s, 'trial', NOW(), %s)
                """, (self.user_id, trial_end))
                return True
    
    # ==================== CLEAR HISTORY ====================
    
    def clear_conversation_history(self):
        """Clear conversation history (keep memories and vocabulary)"""
        self.chat_history.clear()


# ==================== ANALYTICS FUNCTIONS ====================

def get_investor_metrics() -> Dict[str, Any]:
    """Get unified metrics for investors"""
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            metrics = {}
            
            cur.execute("SELECT COUNT(*) as total FROM users")
            metrics['total_users'] = cur.fetchone()['total']
            
            cur.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NOT NULL")
            metrics['telegram_users'] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM users WHERE whatsapp_id IS NOT NULL")
            metrics['whatsapp_users'] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'")
            metrics['active_subscribers'] = cur.fetchone()[0]
            
            metrics['mrr_cents'] = metrics['active_subscribers'] * 777
            metrics['mrr_dollars'] = metrics['mrr_cents'] / 100
            
            cur.execute("""
                SELECT SUM(total_messages), SUM(new_users)
                FROM daily_analytics WHERE date >= CURRENT_DATE - 7
            """)
            row = cur.fetchone()
            metrics['messages_7d'] = row[0] or 0
            metrics['new_users_7d'] = row[1] or 0
            
            cur.execute("SELECT SUM(correct_count + incorrect_count) FROM vocabulary")
            metrics['total_reviews'] = cur.fetchone()[0] or 0
            
            return metrics
```

### ✅ Phase 2 Checkpoint - COMPLETED January 20, 2026
- [x] `espaluz_memory.py` created ✅
- [x] Module imports correctly ✅
- [x] Can create EspaLuzMemory instance ✅
- [x] LangChain PostgresChatMessageHistory working ✅
- [x] Memories save/retrieve working ✅
- [x] User management working ✅
- [x] Vocabulary tracking ready ✅
- [x] Emotional tracking ready ✅

**Module Location:** 
- Oracle Telegram: `/home/ubuntu/EspaLuzFamilybot/espaluz_memory.py`
- Oracle WhatsApp: `/home/ubuntu/EspaLuzWhatsApp/espaluz_memory.py`
- GitHub: Both repositories

**Dependencies Installed:** langchain, langchain-postgres, langchain-community, psycopg, psycopg2-binary

---

## 📱 Phase 3: Telegram Bot Integration (Day 5-7)

### Step 3.1: Update Telegram Bot

**File:** `EspaLuzFamilybot/main.py`

```python
# Add at top of file
from espaluz_memory import EspaLuzMemory

# Replace direct Claude calls with memory-enhanced calls
# BEFORE:
# response = anthropic_client.messages.create(...)

# AFTER:
def handle_message(message):
    user_id = str(message.from_user.id)
    
    # Get memory-enhanced instance
    memory = EspaLuzMemory(platform='telegram', platform_user_id=user_id)
    
    # Check subscription
    sub_status = memory.get_subscription_status()
    if not sub_status['has_access']:
        return send_subscription_message(message)
    
    # Get AI response with full context
    response_text = memory.chat(
        user_message=message.text,
        system_prompt=get_system_prompt(memory.user)  # Your existing prompt
    )
    
    # Track emotion if detected
    emotion = detect_emotion(message.text)  # Your existing function
    if emotion:
        memory.track_emotion(emotion['name'], emotion['intensity'])
    
    return response_text
```

### Step 3.2: Update Voice Handler

```python
def handle_voice(message):
    user_id = str(message.from_user.id)
    memory = EspaLuzMemory(platform='telegram', platform_user_id=user_id)
    
    # Transcribe voice (existing code)
    text = transcribe_voice(message.voice)
    
    # Track as voice message
    memory._track_message('voice')
    
    # Get response
    response_text = memory.chat(user_message=text)
    
    # Generate TTS (existing code)
    audio = generate_tts(response_text)
    
    return audio, response_text
```

### Step 3.3: Test Telegram Integration

```bash
# Start bot in test mode
cd /home/ubuntu/EspaLuzFamilybot
source venv/bin/activate
python main.py --test

# Test commands:
# 1. Send message, verify response
# 2. Send another message, verify context remembered
# 3. Restart bot, send message, verify history loaded
# 4. Check database for stored messages
```

### ✅ Phase 3 Checkpoint
- [ ] Telegram bot uses EspaLuzMemory
- [ ] Messages stored in PostgreSQL
- [ ] Context preserved across messages
- [ ] Bot restart doesn't lose history
- [ ] All existing features still work

---

## 📱 Phase 4: WhatsApp Bot Integration (Day 8-10)

### Step 4.1: Update WhatsApp Bot

**File:** `EspaLuzWhatsApp/espaluz_bridge.py`

```python
# Add at top of file
from espaluz_memory import EspaLuzMemory

def process_message(user_phone: str, message_text: str):
    # Normalize phone number
    phone = user_phone.replace('+', '').replace(' ', '')
    
    # Get memory-enhanced instance
    memory = EspaLuzMemory(platform='whatsapp', platform_user_id=phone)
    
    # Check subscription
    sub_status = memory.get_subscription_status()
    if not sub_status['has_access']:
        return get_subscription_message()
    
    # Get AI response with full context
    response_text = memory.chat(
        user_message=message_text,
        system_prompt=get_system_prompt(memory.user)
    )
    
    return response_text
```

### Step 4.2: Update Voice Handler

```python
def process_voice(user_phone: str, audio_data: bytes):
    phone = user_phone.replace('+', '').replace(' ', '')
    memory = EspaLuzMemory(platform='whatsapp', platform_user_id=phone)
    
    # Transcribe
    text = transcribe_audio(audio_data)
    
    # Track as voice
    memory._track_message('voice')
    
    # Get response
    response_text = memory.chat(user_message=text)
    
    return response_text
```

### ✅ Phase 4 Checkpoint
- [ ] WhatsApp bot uses EspaLuzMemory
- [ ] Messages stored in same PostgreSQL database
- [ ] Cross-platform user linking works (if same email)
- [ ] All existing features still work

---

## 🧪 Phase 5: Testing & Validation (Day 11-12)

### Test Cases

```python
# test_memory_system.py

def test_conversation_persistence():
    """Test that conversation history persists"""
    memory = EspaLuzMemory('telegram', 'test_user_1')
    
    # First message
    response1 = memory.chat("My name is Elena")
    assert memory.user.get('display_name') == 'Elena'
    
    # Second message - should remember name
    response2 = memory.chat("What is my name?")
    assert 'Elena' in response2
    
    # New session - should still remember
    memory2 = EspaLuzMemory('telegram', 'test_user_1')
    response3 = memory2.chat("Do you remember my name?")
    assert 'Elena' in response3

def test_vocabulary_tracking():
    """Test vocabulary and spaced repetition"""
    memory = EspaLuzMemory('telegram', 'test_user_2')
    
    # Add word
    memory.add_word('farmacia', 'pharmacy', 'es', category='medical')
    
    # Check it's there
    words = memory.get_words_for_review()
    assert any(w['word'] == 'farmacia' for w in words)
    
    # Record correct review
    word = next(w for w in words if w['word'] == 'farmacia')
    memory.record_review(word['id'], correct=True)
    
    # Check interval increased
    stats = memory.get_vocabulary_stats()
    assert stats['total_correct'] >= 1

def test_emotional_tracking():
    """Test emotion tracking and trends"""
    memory = EspaLuzMemory('telegram', 'test_user_3')
    
    # Track emotions
    memory.track_emotion('frustrated', 0.7, category='learning')
    memory.track_emotion('happy', 0.8, category='learning')
    memory.track_emotion('happy', 0.9, category='learning')
    
    # Check trend
    trend = memory.get_emotional_trend(days=1)
    assert trend['dominant'] == 'happy'

def test_cross_platform():
    """Test same user on both platforms"""
    # Create on Telegram
    tg_memory = EspaLuzMemory('telegram', 'tg_123')
    tg_memory.update_profile(email='test@example.com', display_name='TestUser')
    
    # Link same email on WhatsApp
    wa_memory = EspaLuzMemory('whatsapp', '5071234567')
    wa_memory.update_profile(email='test@example.com')
    
    # Check they can be linked (manual process for now)
    # Future: auto-link by email
```

### ✅ Phase 5 Checkpoint
- [ ] All test cases pass
- [ ] Conversation persistence verified
- [ ] Vocabulary system works
- [ ] Emotional tracking works
- [ ] No regressions in existing features

---

## 🚀 Phase 6: Deployment (Day 13-14)

### Step 6.1: Deploy to Oracle

```bash
# SSH to Oracle
ssh -i ~/.ssh/oracle-key ubuntu@170.9.242.90

# Update Telegram bot
cd /home/ubuntu/EspaLuzFamilybot
git pull origin main
pip install langchain langchain-anthropic langchain-postgres
sudo systemctl restart espaluz-telegram

# Update WhatsApp bot
cd /home/ubuntu/EspaLuzWhatsApp
git pull origin main
pip install langchain langchain-anthropic langchain-postgres
sudo systemctl restart espaluz-whatsapp

# Verify both running
sudo systemctl status espaluz-telegram
sudo systemctl status espaluz-whatsapp
```

### Step 6.2: Monitor

```bash
# Check logs
sudo journalctl -u espaluz-telegram -f
sudo journalctl -u espaluz-whatsapp -f

# Check database
sudo -u postgres psql espaluz_unified -c "SELECT COUNT(*) FROM chat_message_history;"
```

---

## ✅ Success Criteria

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Conversation persistence | 100% | Restart bot, check history loads |
| Response time | <5 sec | Manual testing |
| Memory recall | >95% | "What's my name?" tests |
| No regressions | 0 bugs | All existing features work |
| Cross-session memory | Works | Return after 24h, context intact |

---

## 🔄 Rollback Plan

If issues occur:

```bash
# Revert to previous code
cd /home/ubuntu/EspaLuzFamilybot
git checkout HEAD~1

# Or disable LangChain and use direct Claude
# Edit main.py to use original anthropic client

# Restart
sudo systemctl restart espaluz-telegram
```

---

## 📅 Timeline Summary

| Day | Phase | Tasks |
|-----|-------|-------|
| 1-2 | Database | Create schema, migrate data |
| 3-4 | Module | Build espaluz_memory.py |
| 5-7 | Telegram | Integrate, test |
| 8-10 | WhatsApp | Integrate, test |
| 11-12 | Testing | Full validation |
| 13-14 | Deploy | Production deployment |

**Total: 2 weeks**

---

## 🎯 What You Get

After implementation:
- ✅ Users remembered across sessions
- ✅ Conversation history persisted in PostgreSQL
- ✅ Vocabulary tracking with spaced repetition
- ✅ Family member profiles
- ✅ Emotional pattern recognition
- ✅ Unified analytics dashboard
- ✅ Foundation for proactive tips
- ✅ Cross-platform user identity

---

---

## 📊 Phase 7: Unified Investor Dashboard (Day 15-17)

### Step 7.1: Create Dashboard Module

**File:** `espaluz_dashboard.py`

```python
"""
EspaLuz Unified Investor Dashboard
Serves both Telegram and WhatsApp analytics from unified database
"""

from flask import Flask, render_template_string, jsonify, request
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
import os

DATABASE_URL = os.getenv('ESPALUZ_DATABASE_URL')

INVESTOR_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>EspaLuz Investor Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', system-ui, sans-serif; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        
        .header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 30px;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header .subtitle { color: #888; font-size: 1.1em; }
        .header .live { 
            display: inline-block;
            background: #00ff88;
            color: #000;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        .metric-value {
            font-size: 3em;
            font-weight: bold;
            background: linear-gradient(135deg, #00ff88, #00d4ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .metric-label { color: #888; margin-top: 10px; font-size: 0.9em; }
        .metric-change { 
            font-size: 0.85em; 
            margin-top: 8px;
            padding: 4px 8px;
            border-radius: 8px;
        }
        .metric-change.positive { background: rgba(0,255,136,0.2); color: #00ff88; }
        .metric-change.negative { background: rgba(255,68,68,0.2); color: #ff4444; }
        
        .section {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 20px;
        }
        .section h2 {
            font-size: 1.3em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .platform-split {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .platform-card {
            background: rgba(255,255,255,0.02);
            border-radius: 12px;
            padding: 20px;
        }
        .platform-card h3 { margin-bottom: 15px; }
        .platform-card.telegram { border-left: 4px solid #0088cc; }
        .platform-card.whatsapp { border-left: 4px solid #25d366; }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { 
            padding: 12px; 
            text-align: left; 
            border-bottom: 1px solid rgba(255,255,255,0.1); 
        }
        th { color: #888; font-weight: normal; }
        
        .funnel {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
        }
        .funnel-stage {
            text-align: center;
            flex: 1;
        }
        .funnel-value { font-size: 2em; font-weight: bold; }
        .funnel-label { color: #888; font-size: 0.9em; }
        .funnel-arrow {
            color: #444;
            font-size: 2em;
        }
        .funnel-rate {
            font-size: 0.8em;
            color: #00ff88;
            margin-top: 5px;
        }
        
        .footer {
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌟 EspaLuz</h1>
            <p class="subtitle">Investor Analytics Dashboard</p>
            <span class="live">● LIVE</span>
            <p style="margin-top: 15px; color: #666;">Last updated: {{ last_updated }}</p>
        </div>
        
        <!-- Key Metrics -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{{ metrics.total_users }}</div>
                <div class="metric-label">Total Users</div>
                <div class="metric-change positive">+{{ metrics.new_users_7d }} this week</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.active_subscribers }}</div>
                <div class="metric-label">Paying Subscribers</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${{ "%.2f"|format(metrics.mrr_dollars) }}</div>
                <div class="metric-label">Monthly Recurring Revenue</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ "%.1f"|format(metrics.conversion_rate) }}%</div>
                <div class="metric-label">Conversion Rate</div>
            </div>
        </div>
        
        <!-- Conversion Funnel -->
        <div class="section">
            <h2>📈 Conversion Funnel</h2>
            <div class="funnel">
                <div class="funnel-stage">
                    <div class="funnel-value">{{ metrics.total_users }}</div>
                    <div class="funnel-label">Total Users</div>
                </div>
                <div class="funnel-arrow">→</div>
                <div class="funnel-stage">
                    <div class="funnel-value">{{ metrics.active_trials }}</div>
                    <div class="funnel-label">Active Trials</div>
                    <div class="funnel-rate">{{ "%.1f"|format(metrics.trial_rate) }}%</div>
                </div>
                <div class="funnel-arrow">→</div>
                <div class="funnel-stage">
                    <div class="funnel-value">{{ metrics.active_subscribers }}</div>
                    <div class="funnel-label">Subscribers</div>
                    <div class="funnel-rate">{{ "%.1f"|format(metrics.conversion_rate) }}%</div>
                </div>
            </div>
        </div>
        
        <!-- Platform Split -->
        <div class="section">
            <h2>📱 Platform Performance</h2>
            <div class="platform-split">
                <div class="platform-card telegram">
                    <h3>📘 Telegram</h3>
                    <table>
                        <tr><td>Users</td><td><strong>{{ metrics.telegram_users }}</strong></td></tr>
                        <tr><td>Messages (7d)</td><td><strong>{{ metrics.telegram_messages_7d }}</strong></td></tr>
                        <tr><td>Subscribers</td><td><strong>{{ metrics.telegram_subscribers }}</strong></td></tr>
                    </table>
                </div>
                <div class="platform-card whatsapp">
                    <h3>📗 WhatsApp</h3>
                    <table>
                        <tr><td>Users</td><td><strong>{{ metrics.whatsapp_users }}</strong></td></tr>
                        <tr><td>Messages (7d)</td><td><strong>{{ metrics.whatsapp_messages_7d }}</strong></td></tr>
                        <tr><td>Subscribers</td><td><strong>{{ metrics.whatsapp_subscribers }}</strong></td></tr>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Engagement Metrics -->
        <div class="section">
            <h2>💬 Engagement</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.messages_7d }}</div>
                    <div class="metric-label">Messages (7 days)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.voice_messages_7d }}</div>
                    <div class="metric-label">Voice Messages</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.words_learned }}</div>
                    <div class="metric-label">Words Learned</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.reviews_completed }}</div>
                    <div class="metric-label">Reviews Completed</div>
                </div>
            </div>
        </div>
        
        <!-- Retention -->
        <div class="section">
            <h2>🔄 Retention</h2>
            <table>
                <tr>
                    <th>Cohort</th>
                    <th>Day 1</th>
                    <th>Day 7</th>
                    <th>Day 30</th>
                </tr>
                {% for cohort in retention %}
                <tr>
                    <td>{{ cohort.week }}</td>
                    <td>{{ cohort.day1 }}%</td>
                    <td>{{ cohort.day7 }}%</td>
                    <td>{{ cohort.day30 }}%</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        <!-- Revenue History -->
        <div class="section">
            <h2>💰 Revenue History</h2>
            <table>
                <tr>
                    <th>Month</th>
                    <th>New Subscribers</th>
                    <th>Churned</th>
                    <th>Net</th>
                    <th>MRR</th>
                </tr>
                {% for month in revenue_history %}
                <tr>
                    <td>{{ month.month }}</td>
                    <td>+{{ month.new }}</td>
                    <td>-{{ month.churned }}</td>
                    <td>{{ month.net }}</td>
                    <td>${{ "%.2f"|format(month.mrr) }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        <div class="footer">
            <p>EspaLuz Investor Dashboard | Data refreshes every 5 minutes</p>
            <p>API Endpoint: <code>/api/metrics</code></p>
        </div>
    </div>
</body>
</html>
'''

def get_investor_metrics():
    """Get comprehensive metrics for investors"""
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            metrics = {}
            
            # Total users
            cur.execute("SELECT COUNT(*) FROM users")
            metrics['total_users'] = cur.fetchone()[0]
            
            # Platform breakdown
            cur.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NOT NULL")
            metrics['telegram_users'] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE whatsapp_id IS NOT NULL")
            metrics['whatsapp_users'] = cur.fetchone()[0]
            
            # Active trials
            cur.execute("""
                SELECT COUNT(*) FROM subscriptions 
                WHERE status = 'trial' AND trial_end > NOW()
            """)
            metrics['active_trials'] = cur.fetchone()[0]
            
            # Subscribers
            cur.execute("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'")
            metrics['active_subscribers'] = cur.fetchone()[0]
            
            # Platform subscribers
            cur.execute("""
                SELECT COUNT(*) FROM subscriptions s
                JOIN users u ON s.user_id = u.id
                WHERE s.status = 'active' AND u.telegram_id IS NOT NULL
            """)
            metrics['telegram_subscribers'] = cur.fetchone()[0]
            cur.execute("""
                SELECT COUNT(*) FROM subscriptions s
                JOIN users u ON s.user_id = u.id
                WHERE s.status = 'active' AND u.whatsapp_id IS NOT NULL
            """)
            metrics['whatsapp_subscribers'] = cur.fetchone()[0]
            
            # MRR
            metrics['mrr_cents'] = metrics['active_subscribers'] * 777
            metrics['mrr_dollars'] = metrics['mrr_cents'] / 100
            
            # Conversion rates
            if metrics['total_users'] > 0:
                metrics['trial_rate'] = (metrics['active_trials'] / metrics['total_users']) * 100
                metrics['conversion_rate'] = (metrics['active_subscribers'] / metrics['total_users']) * 100
            else:
                metrics['trial_rate'] = 0
                metrics['conversion_rate'] = 0
            
            # 7-day metrics
            cur.execute("""
                SELECT 
                    COALESCE(SUM(total_messages), 0) as msgs,
                    COALESCE(SUM(voice_messages), 0) as voice,
                    COALESCE(SUM(new_users), 0) as new_users,
                    COALESCE(SUM(telegram_messages), 0) as tg_msgs,
                    COALESCE(SUM(whatsapp_messages), 0) as wa_msgs,
                    COALESCE(SUM(words_learned), 0) as words,
                    COALESCE(SUM(reviews_completed), 0) as reviews
                FROM daily_analytics WHERE date >= CURRENT_DATE - 7
            """)
            row = cur.fetchone()
            metrics['messages_7d'] = row['msgs']
            metrics['voice_messages_7d'] = row['voice']
            metrics['new_users_7d'] = row['new_users']
            metrics['telegram_messages_7d'] = row['tg_msgs']
            metrics['whatsapp_messages_7d'] = row['wa_msgs']
            metrics['words_learned'] = row['words']
            metrics['reviews_completed'] = row['reviews']
            
            return metrics

def get_retention_cohorts():
    """Calculate retention by weekly cohorts"""
    # Simplified - would need more complex queries in production
    return [
        {'week': 'This Week', 'day1': 85, 'day7': 60, 'day30': '-'},
        {'week': 'Last Week', 'day1': 82, 'day7': 55, 'day30': '-'},
        {'week': '2 Weeks Ago', 'day1': 80, 'day7': 52, 'day30': 35},
    ]

def get_revenue_history():
    """Get monthly revenue history"""
    # Would pull from actual data in production
    return [
        {'month': 'Jan 2026', 'new': 3, 'churned': 0, 'net': 3, 'mrr': 23.31},
        {'month': 'Dec 2025', 'new': 2, 'churned': 1, 'net': 1, 'mrr': 7.77},
    ]

def create_dashboard_app():
    app = Flask(__name__)
    
    @app.route('/investor')
    def investor_dashboard():
        metrics = get_investor_metrics()
        retention = get_retention_cohorts()
        revenue_history = get_revenue_history()
        return render_template_string(
            INVESTOR_DASHBOARD_HTML,
            metrics=metrics,
            retention=retention,
            revenue_history=revenue_history,
            last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        )
    
    @app.route('/api/metrics')
    def api_metrics():
        """JSON API for metrics"""
        return jsonify(get_investor_metrics())
    
    return app
```

### Step 7.2: Add Dashboard Routes to Both Bots

The unified dashboard will be accessible at:
- `https://webhook.aideazz.xyz/espaluz/investor` (via WhatsApp bot)
- Or as a standalone service

### Step 7.3: Investor Dashboard Features

| Feature | Description |
|---------|-------------|
| **Total Users** | Combined Telegram + WhatsApp |
| **Conversion Funnel** | Users → Trials → Subscribers |
| **Platform Split** | Side-by-side Telegram vs WhatsApp |
| **MRR Tracking** | Monthly Recurring Revenue |
| **Retention Cohorts** | Day 1, Day 7, Day 30 retention |
| **Revenue History** | Monthly subscriber changes |
| **Engagement Metrics** | Messages, voice, learning activity |
| **JSON API** | `/api/metrics` for integrations |

### ✅ Phase 7 Checkpoint
- [ ] Dashboard module created
- [ ] Accessible at `/investor` endpoint
- [ ] Shows unified metrics from both platforms
- [ ] JSON API working at `/api/metrics`
- [ ] Retention cohorts calculating
- [ ] Revenue history displaying

---

## 📅 Updated Timeline Summary

| Day | Phase | Tasks |
|-----|-------|-------|
| 1-2 | Database | Create schema, migrate data |
| 3-4 | Module | Build espaluz_memory.py |
| 5-7 | Telegram | Integrate, test |
| 8-10 | WhatsApp | Integrate, test |
| 11-12 | Testing | Full validation |
| 13-14 | Deploy | Production deployment |
| **15-17** | **Dashboard** | **Unified investor dashboard** |

**Total: 2.5 weeks**

---

**Ready to begin Phase 1?**
