"""
EspaLuz Unified Memory System
=============================
Shared memory module for both Telegram and WhatsApp bots.
Uses LangChain + PostgreSQL for intelligent conversation management.

Created: January 20, 2026
Version: 1.0.0

Features:
- Unified user profiles across platforms
- LangChain conversation memory with PostgreSQL backend
- Entity extraction and storage
- Vocabulary tracking with spaced repetition
- Emotional intelligence history
- Family member awareness
- Proactive engagement scheduling
"""

import os
import json
import logging
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from contextlib import contextmanager

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LangChain imports (optional - graceful fallback if not installed)
LANGCHAIN_AVAILABLE = False
PostgresChatMessageHistory = None
ConversationBufferWindowMemory = None

# Try the newer langchain-postgres package first (recommended)
try:
    from langchain_postgres import PostgresChatMessageHistory
    LANGCHAIN_AVAILABLE = True
    logger.debug("Using langchain-postgres (recommended)")
except ImportError:
    # Fallback to langchain-community (deprecated but works)
    try:
        from langchain_community.chat_message_histories import PostgresChatMessageHistory
        LANGCHAIN_AVAILABLE = True
        logger.debug("Using langchain-community PostgresChatMessageHistory")
    except ImportError:
        pass

# Try to import ConversationBufferWindowMemory (optional enhancement)
try:
    from langchain.memory import ConversationBufferWindowMemory
except ImportError:
    try:
        from langchain_core.memory import ConversationBufferWindowMemory
    except ImportError:
        pass

if not LANGCHAIN_AVAILABLE:
    logger.warning("LangChain not installed - using basic memory mode")


@dataclass
class UserProfile:
    """Unified user profile across platforms"""
    id: int = None
    telegram_id: str = None
    whatsapp_id: str = None
    display_name: str = None
    email: str = None
    phone: str = None
    user_type: str = "expat"  # expat, traveler, local
    learning_direction: str = "spanish"  # spanish, english
    preferred_platform: str = None
    preferred_language: str = "es"
    country_of_origin: str = None
    current_country: str = None
    current_city: str = None
    timezone: str = None
    proficiency_level: str = "beginner"
    family_id: str = None
    family_role: str = None
    total_messages: int = 0
    voice_messages: int = 0
    image_messages: int = 0
    streak_days: int = 0
    created_at: datetime = None
    last_active_telegram: datetime = None
    last_active_whatsapp: datetime = None


@dataclass
class FamilyMember:
    """Family member profile"""
    id: int = None
    family_id: str = None
    user_id: int = None
    name: str = None
    nickname: str = None
    relationship: str = None  # parent, child, spouse, etc.
    age: int = None
    age_group: str = None  # child, teen, adult, senior
    proficiency_level: str = None
    interests: List[str] = field(default_factory=list)
    learning_struggles: List[str] = field(default_factory=list)


@dataclass
class VocabularyItem:
    """Vocabulary item with spaced repetition data"""
    id: int = None
    user_id: int = None
    word: str = None
    translation: str = None
    language: str = None
    example_sentence: str = None
    category: str = None
    country_context: str = None
    is_slang: bool = False
    ease_factor: float = 2.5
    interval_days: int = 1
    repetitions: int = 0
    next_review: datetime = None
    correct_count: int = 0
    incorrect_count: int = 0


class EspaLuzMemory:
    """
    Main memory class for EspaLuz bots.
    
    Usage:
        memory = EspaLuzMemory(platform='whatsapp')
        
        # Get or create user
        user = memory.get_or_create_user(whatsapp_id='+1234567890')
        
        # Get conversation memory for LangChain
        chat_memory = memory.get_conversation_memory(user.id)
        
        # Store a memory about the user
        memory.store_user_memory(user.id, 'preference', 'Prefers formal Spanish')
        
        # Track vocabulary
        memory.add_vocabulary(user.id, 'hola', 'hello', 'es')
    """
    
    def __init__(self, platform: str = 'telegram', platform_user_id: str = None, database_url: str = None):
        """
        Initialize memory system for a specific user session.
        
        Args:
            platform: 'telegram' or 'whatsapp'
            platform_user_id: User's ID on that platform (telegram_id or whatsapp_id)
            database_url: PostgreSQL connection string (uses env var if not provided)
        """
        self.platform = platform
        self.platform_user_id = platform_user_id
        self.database_url = database_url or os.getenv(
            'ESPALUZ_UNIFIED_DB_URL',
            os.getenv('DATABASE_URL_UNIFIED')
        )
        self._connection = None
        self._user = None
        self._chat_history = None
        self._test_connection()
        
        # Auto-create user if platform_user_id provided
        if platform_user_id:
            self._init_user()
    
    def _init_user(self):
        """Initialize user based on platform_user_id"""
        if self.platform == 'telegram':
            self._user = self.get_or_create_user(telegram_id=self.platform_user_id)
        else:
            self._user = self.get_or_create_user(whatsapp_id=self.platform_user_id)
        
        # Initialize chat history for this user
        if LANGCHAIN_AVAILABLE and self._user:
            self._chat_history = self.get_conversation_memory(self._user.id)
    
    @property
    def user(self) -> UserProfile:
        """Get the current user profile"""
        return self._user
    
    @property
    def user_id(self) -> int:
        """Get the current user's database ID"""
        return self._user.id if self._user else None
    
    @property
    def chat_history(self):
        """Get LangChain chat history for this user"""
        return self._chat_history
    
    # ==================== SIMPLE TRACKING METHODS ====================
    
    def track_message(self, message_type: str = 'text'):
        """Track a message from the current user"""
        if self._user:
            self.increment_message_count(self._user.id, message_type)
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        if self._user:
            self.add_message_to_history(self._user.id, role, content)
    
    def save_memory(self, content: str, memory_type: str = 'fact', importance: int = 5):
        """Store a memory about the current user"""
        if self._user:
            self.store_user_memory(self._user.id, memory_type, content, importance)
    
    def track_emotion(self, emotion: str, trigger: str = None, intensity: float = 0.5):
        """Track emotional state for current user"""
        if self._user:
            self.record_emotion(self._user.id, emotion, intensity, trigger_summary=trigger)
    
    def add_vocab(self, word: str, translation: str = None, category: str = None):
        """Simple wrapper to add vocabulary for current user"""
        if self._user:
            # Detect language (assume Spanish if not English characters)
            lang = 'es' if any(c in word for c in 'áéíóúñ¿¡') else 'es'
            self.add_vocabulary(
                self._user.id, 
                word, 
                translation or word, 
                lang,
                category=category
            )
    
    def add_family(self, name: str, relationship: str, age: int = None, age_group: str = None):
        """Simple wrapper to add a family member for current user.
        
        Args:
            name: Name of the family member
            relationship: 'spouse', 'child', 'parent', etc.
            age: Age in years (optional)
            age_group: 'toddler', 'child', 'teen', 'adult' (optional)
        """
        if self._user:
            # Create family_id based on user's platform ID
            family_id = self._user.family_id or f"family_{self.platform_user_id}"
            
            # Update user's family_id if not set
            if not self._user.family_id:
                self.update_user(family_id=family_id)
            
            try:
                return self.add_family_member(
                    user_id=self._user.id,
                    family_id=family_id,
                    name=name,
                    relationship=relationship,
                    age=age,
                    age_group=age_group
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to add family member {name}: {e}")
                return None
    
    def _test_connection(self):
        """Test database connection on init"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    logger.info(f"✅ EspaLuz Memory connected to unified database")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager"""
        conn = psycopg2.connect(self.database_url)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # ==================== USER MANAGEMENT ====================
    
    def get_or_create_user(
        self,
        telegram_id: str = None,
        whatsapp_id: str = None,
        display_name: str = None,
        **kwargs
    ) -> UserProfile:
        """
        Get existing user or create new one.
        Handles cross-platform user linking.
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Try to find existing user
                if telegram_id:
                    cur.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
                elif whatsapp_id:
                    cur.execute("SELECT * FROM users WHERE whatsapp_id = %s", (whatsapp_id,))
                else:
                    raise ValueError("Must provide telegram_id or whatsapp_id")
                
                row = cur.fetchone()
                
                if row:
                    # Update last active timestamp
                    if self.platform == 'telegram':
                        cur.execute(
                            "UPDATE users SET last_active_telegram = NOW() WHERE id = %s",
                            (row['id'],)
                        )
                    else:
                        cur.execute(
                            "UPDATE users SET last_active_whatsapp = NOW() WHERE id = %s",
                            (row['id'],)
                        )
                    return self._row_to_user(row)
                
                # Create new user
                cur.execute("""
                    INSERT INTO users (
                        telegram_id, whatsapp_id, display_name, preferred_platform,
                        user_type, learning_direction, preferred_language,
                        current_country, proficiency_level, created_at,
                        last_active_telegram, last_active_whatsapp
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(),
                        CASE WHEN %s = 'telegram' THEN NOW() ELSE NULL END,
                        CASE WHEN %s = 'whatsapp' THEN NOW() ELSE NULL END
                    )
                    RETURNING *
                """, (
                    telegram_id, whatsapp_id, display_name, self.platform,
                    kwargs.get('user_type', 'expat'),
                    kwargs.get('learning_direction', 'spanish'),
                    kwargs.get('preferred_language', 'es'),
                    kwargs.get('current_country'),
                    kwargs.get('proficiency_level', 'beginner'),
                    self.platform, self.platform
                ))
                
                row = cur.fetchone()
                logger.info(f"✨ New user created: {telegram_id or whatsapp_id}")
                return self._row_to_user(row)
    
    def _row_to_user(self, row: dict) -> UserProfile:
        """Convert database row to UserProfile"""
        return UserProfile(
            id=row['id'],
            telegram_id=row.get('telegram_id'),
            whatsapp_id=row.get('whatsapp_id'),
            display_name=row.get('display_name'),
            email=row.get('email'),
            phone=row.get('phone'),
            user_type=row.get('user_type', 'expat'),
            learning_direction=row.get('learning_direction', 'spanish'),
            preferred_platform=row.get('preferred_platform'),
            preferred_language=row.get('preferred_language', 'es'),
            country_of_origin=row.get('country_of_origin'),
            current_country=row.get('current_country'),
            current_city=row.get('current_city'),
            timezone=row.get('timezone'),
            proficiency_level=row.get('proficiency_level', 'beginner'),
            family_id=row.get('family_id'),
            family_role=row.get('family_role'),
            total_messages=row.get('total_messages', 0),
            voice_messages=row.get('voice_messages', 0),
            image_messages=row.get('image_messages', 0),
            streak_days=row.get('streak_days', 0),
            created_at=row.get('created_at'),
            last_active_telegram=row.get('last_active_telegram'),
            last_active_whatsapp=row.get('last_active_whatsapp')
        )
    
    def update_user(self, user_id: int = None, **updates) -> bool:
        """Update user profile fields for the current user or specified user_id"""
        if user_id is None:
            user_id = self.user_id
        if not updates:
            return False
        
        # Build dynamic UPDATE query
        set_clauses = []
        values = []
        for key, value in updates.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)
        
        values.append(user_id)
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE users SET {', '.join(set_clauses)} WHERE id = %s",
                    values
                )
                return cur.rowcount > 0
    
    def increment_message_count(self, user_id: int, message_type: str = 'text'):
        """Increment message counter for user"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                if message_type == 'voice':
                    cur.execute("""
                        UPDATE users SET 
                            voice_messages = voice_messages + 1,
                            total_messages = total_messages + 1
                        WHERE id = %s
                    """, (user_id,))
                elif message_type == 'image':
                    cur.execute("""
                        UPDATE users SET 
                            image_messages = image_messages + 1,
                            total_messages = total_messages + 1
                        WHERE id = %s
                    """, (user_id,))
                else:
                    # text or default
                    cur.execute("""
                        UPDATE users SET 
                            total_messages = total_messages + 1
                        WHERE id = %s
                    """, (user_id,))
    
    # ==================== LANGCHAIN CONVERSATION MEMORY ====================

    @staticmethod
    def session_uuid_for(platform: str, user_id: int) -> str:
        """Deterministic UUID shared by LangChain, RAG, and SQL history."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{platform}_{user_id}"))

    def get_session_uuid(self, user_id: int) -> str:
        return self.session_uuid_for(self.platform, user_id)

    def get_legacy_session_id(self, user_id: int) -> str:
        """Pre-2026 string session_id — kept for reading old rows only."""
        return f"{self.platform}_{user_id}"
    
    def get_conversation_memory(self, user_id: int, window_size: int = 10):
        """
        Get LangChain conversation memory for a user.
        
        Returns PostgresChatMessageHistory backed by PostgreSQL.
        If ConversationBufferWindowMemory is available, wraps it for window management.
        """
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain not available - returning None")
            return None
        
        # Generate a deterministic UUID from platform + user_id
        # This ensures the same user always gets the same session UUID
        session_uuid = self.get_session_uuid(user_id)
        
        try:
            # Create PostgreSQL-backed chat history
            # langchain-postgres: table_name and session_id are positional-only
            sync_conn = self._create_sync_connection()
            chat_history = PostgresChatMessageHistory(
                "chat_message_history",  # table_name (positional)
                session_uuid,            # session_id (positional, must be UUID)
                sync_connection=sync_conn
            )
            
            # Try to wrap in ConversationBufferWindowMemory if available
            if ConversationBufferWindowMemory is not None:
                try:
                    memory = ConversationBufferWindowMemory(
                        chat_memory=chat_history,
                        k=window_size,
                        return_messages=True,
                        memory_key="chat_history"
                    )
                    return memory
                except Exception as e:
                    logger.warning(f"Could not create ConversationBufferWindowMemory: {e}")
            
            # Return raw chat history if wrapper not available
            return chat_history
            
        except Exception as e:
            logger.warning(f"LangChain PostgresChatMessageHistory failed: {e}")
            return None
    
    def _create_sync_connection(self):
        """Create a psycopg3 sync connection for langchain-postgres"""
        try:
            import psycopg
            return psycopg.connect(self.database_url)
        except ImportError:
            logger.warning("psycopg3 not installed - LangChain memory unavailable")
            return None
        except Exception as e:
            logger.error(f"Failed to create psycopg connection: {e}")
            return None
    
    def add_message_to_history(self, user_id: int, role: str, content: str):
        """
        Add a message to conversation history.
        Works even without LangChain installed.
        Uses UUID session_id (same as LangChain + RAG).
        """
        session_id = self.get_session_uuid(user_id)
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                message_data = {
                    "type": "human" if role == "user" else "ai",
                    "data": {"content": content}
                }
                cur.execute("""
                    INSERT INTO chat_message_history (session_id, message, created_at)
                    VALUES (%s, %s, NOW())
                """, (session_id, Json(message_data)))
    
    def get_recent_messages(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get recent messages from conversation history (UUID + legacy string rows)."""
        session_uuid = self.get_session_uuid(user_id)
        legacy_id = self.get_legacy_session_id(user_id)
        
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT message, created_at 
                    FROM chat_message_history 
                    WHERE session_id IN (%s, %s)
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (session_uuid, legacy_id, limit))
                
                rows = cur.fetchall()
                return [
                    {
                        "role": "user" if r['message'].get('type') == 'human' else "assistant",
                        "content": r['message'].get('data', {}).get('content', ''),
                        "timestamp": r['created_at']
                    }
                    for r in reversed(rows)
                ]
    
    # ==================== USER MEMORIES (Key Facts) ====================
    
    def store_user_memory(
        self,
        user_id: int,
        memory_type: str,
        content: str,
        importance: int = 5,
        category: str = None,
        expires_days: int = None
    ):
        """
        Store a key fact/memory about the user.
        
        Memory types: preference, fact, goal, struggle, achievement, family, location
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                expires_at = None
                if expires_days:
                    expires_at = datetime.now() + timedelta(days=expires_days)
                
                cur.execute("""
                    INSERT INTO user_memories (user_id, memory_type, content, importance, category, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (user_id, memory_type, content, importance, category, expires_at))
                
                logger.debug(f"Stored memory for user {user_id}: {memory_type}")
    
    def get_user_memories(
        self,
        user_id: int,
        memory_type: str = None,
        limit: int = 20
    ) -> List[Dict]:
        """Retrieve user memories, optionally filtered by type"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if memory_type:
                    cur.execute("""
                        SELECT * FROM user_memories 
                        WHERE user_id = %s AND memory_type = %s AND is_active = TRUE
                        AND (expires_at IS NULL OR expires_at > NOW())
                        ORDER BY importance DESC, created_at DESC
                        LIMIT %s
                    """, (user_id, memory_type, limit))
                else:
                    cur.execute("""
                        SELECT * FROM user_memories 
                        WHERE user_id = %s AND is_active = TRUE
                        AND (expires_at IS NULL OR expires_at > NOW())
                        ORDER BY importance DESC, created_at DESC
                        LIMIT %s
                    """, (user_id, limit))
                
                return [dict(row) for row in cur.fetchall()]
    
    def get_context_for_prompt(self, user_id: int) -> str:
        """
        Get formatted context string for including in AI prompts.
        Combines user profile + memories + recent vocabulary.
        """
        # Get user profile
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user_row = cur.fetchone()
        
        if not user_row:
            return ""
        
        user = self._row_to_user(user_row)
        memories = self.get_user_memories(user_id, limit=10)
        
        # Build context string
        context_parts = []
        
        # User basics
        if user.display_name:
            context_parts.append(f"User: {user.display_name}")
        if user.user_type:
            context_parts.append(f"Type: {user.user_type}")
        if user.current_country:
            context_parts.append(f"Location: {user.current_country}")
        if user.proficiency_level:
            context_parts.append(f"Level: {user.proficiency_level}")
        if user.learning_direction:
            context_parts.append(f"Learning: {user.learning_direction}")
        
        # Key memories
        if memories:
            context_parts.append("\nKey facts about this user:")
            for mem in memories[:5]:
                context_parts.append(f"- {mem['content']}")
        
        return "\n".join(context_parts)
    
    # ==================== VOCABULARY TRACKING ====================
    
    def add_vocabulary(
        self,
        user_id: int,
        word: str,
        translation: str,
        language: str,
        example_sentence: str = None,
        category: str = None,
        country_context: str = None,
        is_slang: bool = False
    ) -> bool:
        """Add or update a vocabulary item"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO vocabulary (
                        user_id, word, translation, language, example_sentence,
                        category, country_context, is_slang, next_review, learned_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW() + INTERVAL '1 day', NOW())
                    ON CONFLICT (user_id, word, language) DO UPDATE SET
                        translation = EXCLUDED.translation,
                        example_sentence = COALESCE(EXCLUDED.example_sentence, vocabulary.example_sentence)
                    RETURNING id
                """, (user_id, word.lower(), translation, language, example_sentence,
                      category, country_context, is_slang))
                return cur.fetchone() is not None
    
    def get_words_for_review(self, user_id: int, limit: int = 5) -> List[VocabularyItem]:
        """Get vocabulary items due for review (spaced repetition)"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM vocabulary 
                    WHERE user_id = %s AND next_review <= NOW()
                    ORDER BY next_review ASC
                    LIMIT %s
                """, (user_id, limit))
                
                return [VocabularyItem(**dict(row)) for row in cur.fetchall()]
    
    def record_vocabulary_review(self, vocab_id: int, correct: bool):
        """
        Record a vocabulary review result using SM-2 algorithm.
        Updates ease_factor, interval_days, and next_review.
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get current values
                cur.execute("SELECT * FROM vocabulary WHERE id = %s", (vocab_id,))
                vocab = cur.fetchone()
                if not vocab:
                    return
                
                ease_factor = vocab['ease_factor']
                interval = vocab['interval_days']
                reps = vocab['repetitions']
                
                if correct:
                    # SM-2: Correct answer
                    if reps == 0:
                        interval = 1
                    elif reps == 1:
                        interval = 6
                    else:
                        interval = int(interval * ease_factor)
                    
                    reps += 1
                    ease_factor = max(1.3, ease_factor + 0.1)
                    
                    cur.execute("""
                        UPDATE vocabulary SET
                            correct_count = correct_count + 1,
                            ease_factor = %s,
                            interval_days = %s,
                            repetitions = %s,
                            next_review = NOW() + INTERVAL '%s days',
                            last_reviewed = NOW()
                        WHERE id = %s
                    """, (ease_factor, interval, reps, interval, vocab_id))
                else:
                    # SM-2: Incorrect answer - reset
                    ease_factor = max(1.3, ease_factor - 0.2)
                    
                    cur.execute("""
                        UPDATE vocabulary SET
                            incorrect_count = incorrect_count + 1,
                            ease_factor = %s,
                            interval_days = 1,
                            repetitions = 0,
                            next_review = NOW() + INTERVAL '1 day',
                            last_reviewed = NOW()
                        WHERE id = %s
                    """, (ease_factor, vocab_id))
    
    # ==================== EMOTIONAL INTELLIGENCE ====================
    
    def record_emotion(
        self,
        user_id: int,
        emotion: str,
        intensity: float = 0.5,
        category: str = None,
        trigger_summary: str = None,
        response_tone: str = None
    ):
        """Record detected emotion for user"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO emotional_history 
                    (user_id, emotion, intensity, category, platform, trigger_summary, response_tone)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, emotion, intensity, category, self.platform, trigger_summary, response_tone))
    
    def get_emotional_trend(self, user_id: int, days: int = 7) -> Dict:
        """Get emotional trend for user over specified days"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT emotion, COUNT(*) as count, AVG(intensity) as avg_intensity
                    FROM emotional_history
                    WHERE user_id = %s AND detected_at > NOW() - INTERVAL '%s days'
                    GROUP BY emotion
                    ORDER BY count DESC
                """, (user_id, days))
                
                return {row['emotion']: {'count': row['count'], 'intensity': row['avg_intensity']} 
                        for row in cur.fetchall()}
    
    # ==================== FAMILY MANAGEMENT ====================
    
    def add_family_member(
        self,
        user_id: int,
        family_id: str,
        name: str,
        relationship: str = None,
        **kwargs
    ) -> FamilyMember:
        """Add a family member"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Update user's family_id if not set
                cur.execute(
                    "UPDATE users SET family_id = %s WHERE id = %s AND family_id IS NULL",
                    (family_id, user_id)
                )
                
                cur.execute("""
                    INSERT INTO family_members 
                    (family_id, user_id, name, nickname, relationship, age, age_group, 
                     proficiency_level, interests, learning_struggles)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    family_id, user_id, name,
                    kwargs.get('nickname'),
                    relationship,
                    kwargs.get('age'),
                    kwargs.get('age_group'),
                    kwargs.get('proficiency_level'),
                    kwargs.get('interests', []),
                    kwargs.get('learning_struggles', [])
                ))
                
                row = cur.fetchone()
                return FamilyMember(**dict(row))
    
    def get_family_members(self, family_id: str) -> List[FamilyMember]:
        """Get all members of a family"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM family_members WHERE family_id = %s",
                    (family_id,)
                )
                return [FamilyMember(**dict(row)) for row in cur.fetchall()]
    
    # ==================== ANALYTICS ====================
    
    def record_daily_analytics(self):
        """Record daily analytics snapshot"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO daily_analytics (date, telegram_messages, whatsapp_messages, 
                        telegram_users, whatsapp_users, total_messages, new_users, active_users)
                    SELECT 
                        CURRENT_DATE,
                        (SELECT COUNT(*) FROM chat_message_history 
                         WHERE session_id LIKE 'telegram_%' AND created_at::date = CURRENT_DATE),
                        (SELECT COUNT(*) FROM chat_message_history 
                         WHERE session_id LIKE 'whatsapp_%' AND created_at::date = CURRENT_DATE),
                        (SELECT COUNT(*) FROM users WHERE telegram_id IS NOT NULL),
                        (SELECT COUNT(*) FROM users WHERE whatsapp_id IS NOT NULL),
                        (SELECT COUNT(*) FROM chat_message_history WHERE created_at::date = CURRENT_DATE),
                        (SELECT COUNT(*) FROM users WHERE created_at::date = CURRENT_DATE),
                        (SELECT COUNT(DISTINCT COALESCE(
                            CASE WHEN last_active_telegram::date = CURRENT_DATE THEN id END,
                            CASE WHEN last_active_whatsapp::date = CURRENT_DATE THEN id END
                        )) FROM users)
                    ON CONFLICT (date) DO UPDATE SET
                        telegram_messages = EXCLUDED.telegram_messages,
                        whatsapp_messages = EXCLUDED.whatsapp_messages,
                        total_messages = EXCLUDED.total_messages,
                        active_users = EXCLUDED.active_users
                """)
    
    # ==================== EVENT LOGGING ====================
    
    def log_event(self, user_id: int, event_type: str, event_data: Dict = None):
        """Log an event for analytics/debugging"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO event_log (user_id, event_type, platform, event_data)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, event_type, self.platform, Json(event_data or {})))


# ==================== CONVENIENCE FUNCTIONS ====================

def get_memory_for_telegram() -> EspaLuzMemory:
    """Get memory instance configured for Telegram"""
    return EspaLuzMemory(platform='telegram')

def get_memory_for_whatsapp() -> EspaLuzMemory:
    """Get memory instance configured for WhatsApp"""
    return EspaLuzMemory(platform='whatsapp')


# ==================== TEST ====================

if __name__ == "__main__":
    print("Testing EspaLuz Memory System...")
    
    try:
        # Test WhatsApp memory
        memory = get_memory_for_whatsapp()
        print("✅ WhatsApp memory initialized")
        
        # Test getting/creating user
        user = memory.get_or_create_user(whatsapp_id='+test123456')
        print(f"✅ User: {user.id}, WhatsApp: {user.whatsapp_id}")
        
        # Test storing memory
        memory.store_user_memory(user.id, 'preference', 'Test preference')
        print("✅ Memory stored")
        
        # Test getting context
        context = memory.get_context_for_prompt(user.id)
        print(f"✅ Context generated: {len(context)} chars")
        
        # Test LangChain memory
        if LANGCHAIN_AVAILABLE:
            conv_memory = memory.get_conversation_memory(user.id)
            print(f"✅ LangChain memory: {type(conv_memory)}")
        else:
            print("⚠️ LangChain not installed - skipping memory test")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
