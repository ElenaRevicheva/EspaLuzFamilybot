# 🗄️ EspaLuz Unified PostgreSQL Schema

## Pure PostgreSQL Implementation - Both Bots

**Status:** ✅ IMPLEMENTED & WORKING · RAG LIVE (June 30, 2026)  
**Created:** January 19, 2026  
**Updated:** June 30, 2026  
**Cost:** $0 (Oracle Cloud Free Tier)

**Live Database Stats (Oracle, June 30, 2026):**
- users: 19 | chat_message_history: 344 | espaluz_embeddings: 82 (RAG)
- emotional_history: 133 | vocabulary: 75 | user_memories: 13 | subscriptions: 12

Migration for RAG table: `EspaLuzWhatsApp/config/migrations/001_espaluz_embeddings.sql`

---

## 🎯 Objective

Create a **single PostgreSQL database** that serves both Telegram and WhatsApp EspaLuz bots with:
- Shared user profiles (cross-platform identity)
- Unified analytics (single investor dashboard)
- Common learning features (vocabulary, progress)
- Shared subscription management

---

## 📊 Current State (Before Unification)

### WhatsApp Database (`espaluz_whatsapp`)
| Table | Records | Purpose |
|-------|---------|---------|
| `whatsapp_users` | ~10 | User tracking, analytics |
| `daily_stats` | ~30 | Daily metrics |
| `user_trials` | ~10 | Trial management |
| `subscribers` | ~5 | Payment verification |

### Telegram Database (`espaluz_telegram`)
| Table | Records | Purpose |
|-------|---------|---------|
| `telegram_users` | ~15 | User tracking, analytics |
| `telegram_trials` | ~15 | Trial management |
| `telegram_subscriptions` | ~3 | Payment verification |
| `daily_metrics` | ~30 | Daily metrics |
| `event_log` | ~100 | Event tracking |

**Problems:**
- ❌ Duplicate schemas
- ❌ No cross-platform user identity
- ❌ Separate analytics
- ❌ No shared learning features

---

## 🏗️ Unified Schema Design

### Database: `espaluz_unified`

```sql
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
    user_type VARCHAR(20) DEFAULT 'expat',  -- 'expat', 'traveler', 'local'
    learning_direction VARCHAR(20) DEFAULT 'spanish',  -- 'spanish', 'english', 'both'
    primary_goal TEXT,
    
    -- Preferred Communication
    preferred_platform VARCHAR(20),  -- 'telegram', 'whatsapp'
    preferred_language VARCHAR(10) DEFAULT 'es',
    
    -- Location Context
    country_of_origin VARCHAR(50),
    current_country VARCHAR(50),
    current_city VARCHAR(100),
    timezone VARCHAR(50),
    
    -- Learning Profile
    proficiency_level VARCHAR(30) DEFAULT 'beginner',
    
    -- Family Link
    family_id UUID,
    family_role VARCHAR(30),  -- 'parent', 'child', 'solo'
    
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
    
    -- At least one platform ID required
    CONSTRAINT at_least_one_platform CHECK (
        telegram_id IS NOT NULL OR whatsapp_id IS NOT NULL
    )
);

-- ============================================================
-- 2. FAMILY MEMBERS
-- ============================================================
CREATE TABLE family_members (
    id SERIAL PRIMARY KEY,
    family_id UUID NOT NULL,
    user_id INTEGER REFERENCES users(id),
    
    -- Member Info
    name VARCHAR(100) NOT NULL,
    nickname VARCHAR(50),
    relationship VARCHAR(30),  -- 'spouse', 'child', 'parent', 'self'
    age INTEGER,
    age_group VARCHAR(20),     -- 'toddler', 'child', 'teen', 'adult'
    
    -- Learning Profile
    proficiency_level VARCHAR(30),
    interests TEXT[],
    learning_struggles TEXT[],
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 3. UNIFIED SUBSCRIPTION MANAGEMENT
-- ============================================================
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    
    -- Subscription Details
    status VARCHAR(20) DEFAULT 'trial',  -- 'trial', 'active', 'cancelled', 'expired'
    source VARCHAR(30),  -- 'paypal', 'crypto', 'manual'
    
    -- PayPal Data
    paypal_subscription_id VARCHAR(100) UNIQUE,
    paypal_plan_id VARCHAR(100),
    
    -- Trial Info
    trial_start TIMESTAMP,
    trial_end TIMESTAMP,
    
    -- Subscription Dates
    started_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    expires_at TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 4. CONVERSATION MEMORY (Key Facts - Not Full History)
-- ============================================================
CREATE TABLE user_memories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    
    -- Memory Content
    memory_type VARCHAR(30) NOT NULL,  -- 'fact', 'preference', 'struggle', 'achievement', 'goal'
    content TEXT NOT NULL,
    importance INTEGER DEFAULT 5,  -- 1-10
    
    -- Context
    category VARCHAR(50),  -- 'learning', 'family', 'relocation', 'personal'
    source_platform VARCHAR(20),  -- Where this was learned
    
    -- Usage
    times_used INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    
    -- Lifecycle
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,  -- Some memories expire
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- 5. VOCABULARY TRACKING (Spaced Repetition)
-- ============================================================
CREATE TABLE vocabulary (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    family_member_id INTEGER REFERENCES family_members(id),
    
    -- Word Data
    word VARCHAR(100) NOT NULL,
    translation VARCHAR(100) NOT NULL,
    language VARCHAR(10) NOT NULL,  -- 'es' or 'en'
    example_sentence TEXT,
    category VARCHAR(50),  -- 'banking', 'medical', 'food', 'travel'
    
    -- Country Variant
    country_context VARCHAR(50),  -- 'mexico', 'spain', 'colombia', 'panama'
    is_slang BOOLEAN DEFAULT FALSE,
    
    -- Spaced Repetition (SM-2 Algorithm)
    ease_factor FLOAT DEFAULT 2.5,
    interval_days INTEGER DEFAULT 1,
    repetitions INTEGER DEFAULT 0,
    next_review TIMESTAMP,
    last_reviewed TIMESTAMP,
    
    -- Performance
    correct_count INTEGER DEFAULT 0,
    incorrect_count INTEGER DEFAULT 0,
    
    -- Source
    learned_from VARCHAR(50),  -- 'conversation', 'lesson', 'correction'
    learned_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, word, language)
);

-- ============================================================
-- 6. EMOTIONAL HISTORY
-- ============================================================
CREATE TABLE emotional_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    
    -- Emotion Data
    emotion VARCHAR(50) NOT NULL,
    intensity FLOAT,  -- 0.0 to 1.0
    category VARCHAR(50),  -- 'learning', 'cultural', 'family', 'relocation'
    
    -- Context
    platform VARCHAR(20),
    trigger_summary TEXT,
    
    -- Bot Response
    response_tone VARCHAR(50),
    
    detected_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 7. UNIFIED DAILY ANALYTICS
-- ============================================================
CREATE TABLE daily_analytics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    
    -- Platform Breakdown
    telegram_messages INTEGER DEFAULT 0,
    whatsapp_messages INTEGER DEFAULT 0,
    telegram_users INTEGER DEFAULT 0,
    whatsapp_users INTEGER DEFAULT 0,
    
    -- Combined Metrics
    total_messages INTEGER DEFAULT 0,
    voice_messages INTEGER DEFAULT 0,
    image_messages INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    
    -- Learning Metrics
    words_learned INTEGER DEFAULT 0,
    reviews_completed INTEGER DEFAULT 0,
    
    -- Business Metrics
    trials_started INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    cancellations INTEGER DEFAULT 0,
    mrr_cents INTEGER DEFAULT 0,
    
    UNIQUE(date)
);

-- ============================================================
-- 8. SCHEDULED MESSAGES (Proactive Tips)
-- ============================================================
CREATE TABLE scheduled_messages (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    
    -- Message Content
    message_type VARCHAR(30) NOT NULL,  -- 'review', 'tip', 'holiday', 'streak'
    platform VARCHAR(20) NOT NULL,  -- 'telegram', 'whatsapp'
    content TEXT,
    content_data JSONB,
    
    -- Schedule
    scheduled_for TIMESTAMP NOT NULL,
    
    -- Delivery
    sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP,
    
    -- Response
    user_engaged BOOLEAN,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 9. RELOCATION MILESTONES (For Expats)
-- ============================================================
CREATE TABLE relocation_milestones (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    
    -- Milestone
    milestone_type VARCHAR(50) NOT NULL,  -- 'visa', 'housing', 'school', 'bank'
    title VARCHAR(200),
    status VARCHAR(20) DEFAULT 'not_started',
    
    -- Dates
    target_date DATE,
    completed_date DATE,
    
    -- Notes
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 10. EVENT LOG (Debugging & Analytics)
-- ============================================================
CREATE TABLE event_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    
    -- Event
    event_type VARCHAR(50) NOT NULL,
    platform VARCHAR(20),
    event_data JSONB,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================
CREATE INDEX idx_users_telegram ON users(telegram_id) WHERE telegram_id IS NOT NULL;
CREATE INDEX idx_users_whatsapp ON users(whatsapp_id) WHERE whatsapp_id IS NOT NULL;
CREATE INDEX idx_users_email ON users(email) WHERE email IS NOT NULL;
CREATE INDEX idx_users_family ON users(family_id) WHERE family_id IS NOT NULL;

CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_paypal ON subscriptions(paypal_subscription_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

CREATE INDEX idx_vocabulary_user_review ON vocabulary(user_id, next_review);
CREATE INDEX idx_vocabulary_category ON vocabulary(category);

CREATE INDEX idx_emotional_user_date ON emotional_history(user_id, detected_at);

CREATE INDEX idx_scheduled_pending ON scheduled_messages(scheduled_for, sent) 
    WHERE sent = FALSE;

CREATE INDEX idx_daily_analytics_date ON daily_analytics(date);

CREATE INDEX idx_event_log_user ON event_log(user_id, created_at);
```

---

## 🔄 Data Migration Plan

### Step 1: Create New Database
```sql
CREATE DATABASE espaluz_unified;
CREATE USER espaluz_app WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE espaluz_unified TO espaluz_app;
```

### Step 2: Migrate WhatsApp Users
```sql
-- Insert WhatsApp users into unified table
INSERT INTO users (whatsapp_id, display_name, current_country, total_messages, 
                   voice_messages, image_messages, streak_days, created_at, last_active_whatsapp)
SELECT 
    user_id,
    NULL,  -- display_name not stored
    countries[1],  -- First country
    total_messages,
    voice_messages,
    image_messages,
    streak_days,
    first_seen,
    last_seen
FROM espaluz_whatsapp.whatsapp_users;
```

### Step 3: Migrate Telegram Users
```sql
-- Insert Telegram users (or update if email matches)
INSERT INTO users (telegram_id, display_name, current_country, total_messages,
                   voice_messages, image_messages, created_at, last_active_telegram)
SELECT 
    user_id,
    first_name,
    country,
    total_messages,
    voice_messages,
    image_messages,
    first_seen,
    last_active
FROM espaluz_telegram.telegram_users
ON CONFLICT (email) DO UPDATE SET
    telegram_id = EXCLUDED.telegram_id,
    last_active_telegram = EXCLUDED.last_active_telegram;
```

### Step 4: Migrate Subscriptions
```sql
-- Merge subscription data from both platforms
INSERT INTO subscriptions (user_id, status, source, paypal_subscription_id, trial_start, trial_end)
SELECT 
    u.id,
    CASE WHEN s.status = 'active' THEN 'active' ELSE 'trial' END,
    'paypal',
    s.paypal_subscription_id,
    t.trial_start,
    t.trial_end
FROM espaluz_whatsapp.subscribers s
JOIN users u ON u.whatsapp_id = s.whatsapp_id
LEFT JOIN espaluz_whatsapp.user_trials t ON t.user_id = s.whatsapp_id;
```

---

## 📊 Shared Python Module

### `espaluz_db.py` (Used by Both Bots)

```python
"""
EspaLuz Unified Database Module
Shared between Telegram and WhatsApp bots
"""

import os
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://espaluz_app:password@localhost:5432/espaluz_unified')


class EspaLuzDB:
    """Unified database operations for both bots"""
    
    def __init__(self):
        self.database_url = DATABASE_URL
    
    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(self.database_url)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # ==================== USER OPERATIONS ====================
    
    def get_or_create_user(self, platform: str, platform_id: str) -> Dict[str, Any]:
        """Get existing user or create new one"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Try to find existing user
                if platform == 'telegram':
                    cur.execute("SELECT * FROM users WHERE telegram_id = %s", (platform_id,))
                else:
                    cur.execute("SELECT * FROM users WHERE whatsapp_id = %s", (platform_id,))
                
                user = cur.fetchone()
                
                if user:
                    # Update last active
                    if platform == 'telegram':
                        cur.execute("UPDATE users SET last_active_telegram = NOW() WHERE id = %s", (user['id'],))
                    else:
                        cur.execute("UPDATE users SET last_active_whatsapp = NOW() WHERE id = %s", (user['id'],))
                    return dict(user)
                
                # Create new user
                if platform == 'telegram':
                    cur.execute("""
                        INSERT INTO users (telegram_id, last_active_telegram)
                        VALUES (%s, NOW()) RETURNING *
                    """, (platform_id,))
                else:
                    cur.execute("""
                        INSERT INTO users (whatsapp_id, last_active_whatsapp)
                        VALUES (%s, NOW()) RETURNING *
                    """, (platform_id,))
                
                return dict(cur.fetchone())
    
    def update_user_profile(self, user_id: int, **kwargs) -> bool:
        """Update user profile fields"""
        allowed_fields = ['display_name', 'email', 'phone', 'user_type', 
                         'learning_direction', 'primary_goal', 'country_of_origin',
                         'current_country', 'current_city', 'timezone', 
                         'proficiency_level', 'family_id', 'family_role']
        
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False
        
        set_clause = ', '.join(f"{k} = %s" for k in updates.keys())
        values = list(updates.values()) + [user_id]
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"UPDATE users SET {set_clause} WHERE id = %s", values)
                return cur.rowcount > 0
    
    def link_platforms(self, user_id: int, telegram_id: str = None, whatsapp_id: str = None) -> bool:
        """Link a user account to another platform"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                if telegram_id:
                    cur.execute("UPDATE users SET telegram_id = %s WHERE id = %s", (telegram_id, user_id))
                if whatsapp_id:
                    cur.execute("UPDATE users SET whatsapp_id = %s WHERE id = %s", (whatsapp_id, user_id))
                return True
    
    # ==================== MESSAGE TRACKING ====================
    
    def track_message(self, user_id: int, platform: str, message_type: str = 'text') -> bool:
        """Track a message and update analytics"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Update user stats
                if message_type == 'voice':
                    cur.execute("""
                        UPDATE users SET total_messages = total_messages + 1,
                                        voice_messages = voice_messages + 1
                        WHERE id = %s
                    """, (user_id,))
                elif message_type == 'image':
                    cur.execute("""
                        UPDATE users SET total_messages = total_messages + 1,
                                        image_messages = image_messages + 1
                        WHERE id = %s
                    """, (user_id,))
                else:
                    cur.execute("UPDATE users SET total_messages = total_messages + 1 WHERE id = %s", (user_id,))
                
                # Update daily analytics
                today = datetime.now().date()
                telegram_inc = 1 if platform == 'telegram' else 0
                whatsapp_inc = 1 if platform == 'whatsapp' else 0
                voice_inc = 1 if message_type == 'voice' else 0
                image_inc = 1 if message_type == 'image' else 0
                
                cur.execute("""
                    INSERT INTO daily_analytics (date, telegram_messages, whatsapp_messages, 
                                                total_messages, voice_messages, image_messages)
                    VALUES (%s, %s, %s, 1, %s, %s)
                    ON CONFLICT (date) DO UPDATE SET
                        telegram_messages = daily_analytics.telegram_messages + %s,
                        whatsapp_messages = daily_analytics.whatsapp_messages + %s,
                        total_messages = daily_analytics.total_messages + 1,
                        voice_messages = daily_analytics.voice_messages + %s,
                        image_messages = daily_analytics.image_messages + %s
                """, (today, telegram_inc, whatsapp_inc, voice_inc, image_inc,
                      telegram_inc, whatsapp_inc, voice_inc, image_inc))
                
                return True
    
    # ==================== SUBSCRIPTION MANAGEMENT ====================
    
    def get_subscription_status(self, user_id: int) -> Dict[str, Any]:
        """Get user's subscription status"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM subscriptions 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC LIMIT 1
                """, (user_id,))
                sub = cur.fetchone()
                
                if not sub:
                    return {'status': 'none', 'has_access': False}
                
                now = datetime.now()
                
                if sub['status'] == 'active':
                    return {'status': 'active', 'has_access': True, 'subscription': dict(sub)}
                
                if sub['status'] == 'trial' and sub['trial_end'] and sub['trial_end'] > now:
                    days_left = (sub['trial_end'] - now).days
                    return {'status': 'trial', 'has_access': True, 'days_left': days_left}
                
                return {'status': 'expired', 'has_access': False}
    
    def start_trial(self, user_id: int, days: int = 7) -> bool:
        """Start a trial for user"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                trial_end = datetime.now() + timedelta(days=days)
                cur.execute("""
                    INSERT INTO subscriptions (user_id, status, trial_start, trial_end)
                    VALUES (%s, 'trial', NOW(), %s)
                    ON CONFLICT DO NOTHING
                """, (user_id, trial_end))
                return True
    
    def activate_subscription(self, user_id: int, paypal_subscription_id: str) -> bool:
        """Activate a paid subscription"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE subscriptions 
                    SET status = 'active', 
                        paypal_subscription_id = %s,
                        started_at = NOW()
                    WHERE user_id = %s
                """, (paypal_subscription_id, user_id))
                return cur.rowcount > 0
    
    # ==================== MEMORY OPERATIONS ====================
    
    def save_memory(self, user_id: int, memory_type: str, content: str, 
                   category: str = None, importance: int = 5) -> int:
        """Save a memory/fact about the user"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_memories (user_id, memory_type, content, category, importance)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (user_id, memory_type, content, category, importance))
                return cur.fetchone()[0]
    
    def get_memories(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's important memories"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM user_memories 
                    WHERE user_id = %s AND is_active = TRUE
                    ORDER BY importance DESC, created_at DESC
                    LIMIT %s
                """, (user_id, limit))
                return [dict(row) for row in cur.fetchall()]
    
    # ==================== VOCABULARY OPERATIONS ====================
    
    def add_vocabulary(self, user_id: int, word: str, translation: str, 
                      language: str, category: str = None) -> bool:
        """Add a word to user's vocabulary"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                next_review = datetime.now() + timedelta(days=1)
                cur.execute("""
                    INSERT INTO vocabulary (user_id, word, translation, language, category, next_review)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, word, language) DO NOTHING
                """, (user_id, word, translation, language, category, next_review))
                return True
    
    def get_words_for_review(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get words due for review"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM vocabulary 
                    WHERE user_id = %s AND next_review <= NOW()
                    ORDER BY next_review ASC
                    LIMIT %s
                """, (user_id, limit))
                return [dict(row) for row in cur.fetchall()]
    
    def record_review(self, vocab_id: int, correct: bool) -> bool:
        """Record vocabulary review result (SM-2 algorithm)"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get current values
                cur.execute("SELECT * FROM vocabulary WHERE id = %s", (vocab_id,))
                vocab = cur.fetchone()
                
                if not vocab:
                    return False
                
                # SM-2 Algorithm
                ease_factor = vocab['ease_factor']
                interval = vocab['interval_days']
                repetitions = vocab['repetitions']
                
                if correct:
                    if repetitions == 0:
                        interval = 1
                    elif repetitions == 1:
                        interval = 6
                    else:
                        interval = int(interval * ease_factor)
                    
                    repetitions += 1
                    ease_factor = max(1.3, ease_factor + 0.1)
                else:
                    repetitions = 0
                    interval = 1
                    ease_factor = max(1.3, ease_factor - 0.2)
                
                next_review = datetime.now() + timedelta(days=interval)
                
                cur.execute("""
                    UPDATE vocabulary SET
                        ease_factor = %s,
                        interval_days = %s,
                        repetitions = %s,
                        next_review = %s,
                        last_reviewed = NOW(),
                        correct_count = correct_count + %s,
                        incorrect_count = incorrect_count + %s
                    WHERE id = %s
                """, (ease_factor, interval, repetitions, next_review,
                      1 if correct else 0, 0 if correct else 1, vocab_id))
                
                return True
    
    # ==================== EMOTIONAL TRACKING ====================
    
    def track_emotion(self, user_id: int, emotion: str, intensity: float = 0.5,
                     category: str = None, platform: str = None) -> bool:
        """Track detected emotion"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO emotional_history (user_id, emotion, intensity, category, platform)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, emotion, intensity, category, platform))
                return True
    
    def get_emotional_trend(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """Get emotional trend for user"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT emotion, COUNT(*) as count, AVG(intensity) as avg_intensity
                    FROM emotional_history
                    WHERE user_id = %s AND detected_at >= NOW() - INTERVAL '%s days'
                    GROUP BY emotion
                    ORDER BY count DESC
                """, (user_id, days))
                
                emotions = [dict(row) for row in cur.fetchall()]
                
                return {
                    'emotions': emotions,
                    'dominant': emotions[0]['emotion'] if emotions else None,
                    'period_days': days
                }
    
    # ==================== ANALYTICS ====================
    
    def get_investor_metrics(self) -> Dict[str, Any]:
        """Get metrics for investor dashboard"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                metrics = {}
                
                # Total users
                cur.execute("SELECT COUNT(*) as total FROM users")
                metrics['total_users'] = cur.fetchone()['total']
                
                # Platform breakdown
                cur.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NOT NULL")
                metrics['telegram_users'] = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM users WHERE whatsapp_id IS NOT NULL")
                metrics['whatsapp_users'] = cur.fetchone()[0]
                
                # Active subscribers
                cur.execute("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'")
                metrics['active_subscribers'] = cur.fetchone()[0]
                
                # MRR
                metrics['mrr_cents'] = metrics['active_subscribers'] * 777  # $7.77
                metrics['mrr_dollars'] = metrics['mrr_cents'] / 100
                
                # 7-day metrics
                cur.execute("""
                    SELECT SUM(total_messages) as msgs, SUM(new_users) as new_users
                    FROM daily_analytics WHERE date >= CURRENT_DATE - 7
                """)
                row = cur.fetchone()
                metrics['messages_7d'] = row['msgs'] or 0
                metrics['new_users_7d'] = row['new_users'] or 0
                
                return metrics


# Global instance
db = EspaLuzDB()
```

---

## 🎯 What This Enables

| Feature | Before (Separate DBs) | After (Unified) |
|---------|----------------------|-----------------|
| Cross-platform identity | ❌ Impossible | ✅ Same user on Telegram & WhatsApp |
| Unified analytics | ❌ Manual merge | ✅ Single dashboard |
| Shared subscriptions | ❌ Pay twice | ✅ One subscription, both platforms |
| Learning progress | ❌ Not tracked | ✅ Vocabulary + spaced repetition |
| User memories | ❌ Session only | ✅ Persisted across sessions |
| Emotional patterns | ❌ One-shot | ✅ Week-over-week trends |
| Family profiles | ❌ Basic | ✅ Full family support |

---

## 📅 Implementation Order

1. **Week 1:** Create database, migrate existing data
2. **Week 2:** Update both bots to use `espaluz_db.py`
3. **Week 3:** Add vocabulary tracking + review system
4. **Week 4:** Add user memories + emotional tracking
5. **Week 5:** Add proactive messaging (scheduled_messages)
6. **Week 6:** Add family profiles + relocation milestones

---

## 💰 Cost: $0

All on Oracle Cloud Free Tier:
- PostgreSQL: Included
- Storage: <100MB for 1000+ users
- Compute: Already running both bots

---

**See Also:**
- `LANGCHAIN_POSTGRES_BLUEPRINT.md` - Future LangChain integration
- `UNIFIED_VISION_ROADMAP.md` - Overall product vision
- `SWOT_ANALYSIS_ESPALUZ.md` - Strategic analysis
