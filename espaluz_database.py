"""
EspaLuz PostgreSQL Database Module
Investor-Ready Analytics with JSON Fallback

This module adds PostgreSQL tracking WITHOUT breaking existing JSON-based functionality.
All existing code continues to work - this adds database tracking alongside it.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import threading

# Try to import psycopg2, but don't fail if not available
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logging.warning("psycopg2 not available - using JSON fallback only")

# Database connection string
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://espaluz:espaluz_secure_2026@localhost:5432/espaluz_telegram')


class EspaluzDatabase:
    """
    PostgreSQL database for EspaLuz Telegram bot.
    Tracks users, trials, subscriptions, and daily metrics.
    Falls back to JSON if database is unavailable.
    """
    
    def __init__(self):
        self.database_url = DATABASE_URL
        self.use_database = False
        self.lock = threading.Lock()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # JSON fallback files (existing files - don't change them)
        self.json_users_file = os.path.join(self.base_dir, "user_sessions.json")
        self.json_trials_file = os.path.join(self.base_dir, "telegram_trials.json")
        self.json_subscribers_file = os.path.join(self.base_dir, "telegram_subscribers.json")
        
        # Try to connect to database
        self._init_database()
    
    def _init_database(self):
        """Initialize database connection and verify tables exist"""
        if not PSYCOPG2_AVAILABLE:
            logging.warning("📊 Database: psycopg2 not installed, using JSON fallback")
            return
        
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Verify tables exist
                    cur.execute("SELECT COUNT(*) FROM telegram_users")
                    cur.fetchone()
                    self.use_database = True
                    logging.info("✅ Database: PostgreSQL connected successfully")
                    print("✅ Database: PostgreSQL connected successfully")
        except Exception as e:
            logging.warning(f"📊 Database: PostgreSQL unavailable ({e}), using JSON fallback")
            print(f"⚠️ Database: PostgreSQL unavailable ({e}), using JSON fallback")
            self.use_database = False
    
    def _get_connection(self):
        """Get a database connection"""
        if not self.use_database:
            return None
        try:
            return psycopg2.connect(self.database_url)
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            return None
    
    # ==================== USER TRACKING ====================
    
    def track_user(self, user_id: str, username: str = None, first_name: str = None,
                   country: str = None, role: str = None) -> bool:
        """
        Track a user - creates if new, updates last_active if existing.
        This is ADDITIVE - doesn't affect existing JSON tracking.
        """
        if not self.use_database:
            return False
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO telegram_users 
                        (user_id, telegram_username, first_name, country, role, first_seen, last_active)
                        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT (user_id) DO UPDATE SET
                            last_active = CURRENT_TIMESTAMP,
                            telegram_username = COALESCE(EXCLUDED.telegram_username, telegram_users.telegram_username),
                            first_name = COALESCE(EXCLUDED.first_name, telegram_users.first_name),
                            country = COALESCE(EXCLUDED.country, telegram_users.country),
                            role = COALESCE(EXCLUDED.role, telegram_users.role)
                    """, (user_id, username, first_name, country, role))
                    conn.commit()
                    return True
        except Exception as e:
            logging.error(f"Error tracking user: {e}")
            return False
    
    def track_message(self, user_id: str, message_type: str = 'text') -> bool:
        """
        Track a message from a user.
        message_type: 'text', 'voice', 'image'
        """
        if not self.use_database:
            return False
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Update user message count
                    if message_type == 'voice':
                        cur.execute("""
                            UPDATE telegram_users 
                            SET total_messages = total_messages + 1,
                                voice_messages = voice_messages + 1,
                                last_active = CURRENT_TIMESTAMP
                            WHERE user_id = %s
                        """, (user_id,))
                    elif message_type == 'image':
                        cur.execute("""
                            UPDATE telegram_users 
                            SET total_messages = total_messages + 1,
                                image_messages = image_messages + 1,
                                last_active = CURRENT_TIMESTAMP
                            WHERE user_id = %s
                        """, (user_id,))
                    else:
                        cur.execute("""
                            UPDATE telegram_users 
                            SET total_messages = total_messages + 1,
                                last_active = CURRENT_TIMESTAMP
                            WHERE user_id = %s
                        """, (user_id,))
                    
                    # Update daily metrics
                    today = datetime.now().date()
                    if message_type == 'voice':
                        cur.execute("""
                            INSERT INTO daily_metrics (date, total_messages, voice_messages, active_users)
                            VALUES (%s, 1, 1, 1)
                            ON CONFLICT (date) DO UPDATE SET
                                total_messages = daily_metrics.total_messages + 1,
                                voice_messages = daily_metrics.voice_messages + 1
                        """, (today,))
                    elif message_type == 'image':
                        cur.execute("""
                            INSERT INTO daily_metrics (date, total_messages, image_messages, active_users)
                            VALUES (%s, 1, 1, 1)
                            ON CONFLICT (date) DO UPDATE SET
                                total_messages = daily_metrics.total_messages + 1,
                                image_messages = daily_metrics.image_messages + 1
                        """, (today,))
                    else:
                        cur.execute("""
                            INSERT INTO daily_metrics (date, total_messages, active_users)
                            VALUES (%s, 1, 1)
                            ON CONFLICT (date) DO UPDATE SET
                                total_messages = daily_metrics.total_messages + 1
                        """, (today,))
                    
                    conn.commit()
                    return True
        except Exception as e:
            logging.error(f"Error tracking message: {e}")
            return False
    
    # ==================== TRIAL TRACKING ====================
    
    def start_trial(self, user_id: str, trial_days: int = 14) -> bool:
        """Start a trial for a user"""
        if not self.use_database:
            return False
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    trial_end = datetime.now() + timedelta(days=trial_days)
                    
                    # Ensure user exists first
                    cur.execute("""
                        INSERT INTO telegram_users (user_id)
                        VALUES (%s)
                        ON CONFLICT (user_id) DO UPDATE SET status = 'trial'
                    """, (user_id,))
                    
                    # Create trial record
                    cur.execute("""
                        INSERT INTO telegram_trials (user_id, trial_start, trial_end, status)
                        VALUES (%s, CURRENT_TIMESTAMP, %s, 'active')
                        ON CONFLICT (user_id) DO UPDATE SET
                            trial_start = CURRENT_TIMESTAMP,
                            trial_end = EXCLUDED.trial_end,
                            status = 'active'
                    """, (user_id, trial_end))
                    
                    # Update daily metrics
                    today = datetime.now().date()
                    cur.execute("""
                        INSERT INTO daily_metrics (date, trials_started)
                        VALUES (%s, 1)
                        ON CONFLICT (date) DO UPDATE SET
                            trials_started = daily_metrics.trials_started + 1
                    """, (today,))
                    
                    conn.commit()
                    return True
        except Exception as e:
            logging.error(f"Error starting trial: {e}")
            return False
    
    # ==================== SUBSCRIPTION TRACKING ====================
    
    def record_subscription(self, user_id: str, email: str, subscription_id: str,
                           plan_id: str, source: str = 'direct_id') -> bool:
        """Record a verified PayPal subscription"""
        if not self.use_database:
            return False
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Ensure user exists
                    cur.execute("""
                        INSERT INTO telegram_users (user_id, status)
                        VALUES (%s, 'active')
                        ON CONFLICT (user_id) DO UPDATE SET status = 'active'
                    """, (user_id,))
                    
                    # Record subscription
                    cur.execute("""
                        INSERT INTO telegram_subscriptions 
                        (user_id, email, paypal_subscription_id, plan_id, source, status, started_at)
                        VALUES (%s, %s, %s, %s, %s, 'active', CURRENT_TIMESTAMP)
                        ON CONFLICT (paypal_subscription_id) DO UPDATE SET
                            status = 'active',
                            user_id = EXCLUDED.user_id
                    """, (user_id, email, subscription_id, plan_id, source))
                    
                    # Mark trial as converted if exists
                    cur.execute("""
                        UPDATE telegram_trials 
                        SET converted_to_paid = true, converted_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s AND converted_to_paid = false
                    """, (user_id,))
                    
                    # Update daily metrics
                    today = datetime.now().date()
                    cur.execute("""
                        INSERT INTO daily_metrics (date, conversions, mrr_cents)
                        VALUES (%s, 1, 1100)
                        ON CONFLICT (date) DO UPDATE SET
                            conversions = daily_metrics.conversions + 1,
                            mrr_cents = daily_metrics.mrr_cents + 1100
                    """, (today,))
                    
                    conn.commit()
                    
                    # Log event
                    self.log_event(user_id, 'subscription_created', {
                        'email': email,
                        'subscription_id': subscription_id,
                        'plan_id': plan_id,
                        'source': source
                    })
                    
                    return True
        except Exception as e:
            logging.error(f"Error recording subscription: {e}")
            return False
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Mark a subscription as cancelled"""
        if not self.use_database:
            return False
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE telegram_subscriptions 
                        SET status = 'cancelled', cancelled_at = CURRENT_TIMESTAMP
                        WHERE paypal_subscription_id = %s
                        RETURNING user_id
                    """, (subscription_id,))
                    
                    result = cur.fetchone()
                    if result:
                        user_id = result[0]
                        
                        # Update user status
                        cur.execute("""
                            UPDATE telegram_users SET status = 'cancelled' WHERE user_id = %s
                        """, (user_id,))
                        
                        # Update daily metrics
                        today = datetime.now().date()
                        cur.execute("""
                            INSERT INTO daily_metrics (date, cancellations)
                            VALUES (%s, 1)
                            ON CONFLICT (date) DO UPDATE SET
                                cancellations = daily_metrics.cancellations + 1
                        """, (today,))
                    
                    conn.commit()
                    return True
        except Exception as e:
            logging.error(f"Error cancelling subscription: {e}")
            return False
    
    # ==================== EVENT LOGGING ====================
    
    def log_event(self, user_id: str, event_type: str, event_data: Dict = None) -> bool:
        """Log an event for analytics"""
        if not self.use_database:
            return False
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO event_log (user_id, event_type, event_data)
                        VALUES (%s, %s, %s)
                    """, (user_id, event_type, json.dumps(event_data or {})))
                    conn.commit()
                    return True
        except Exception as e:
            logging.error(f"Error logging event: {e}")
            return False
    
    # ==================== ANALYTICS QUERIES ====================
    
    def get_investor_metrics(self) -> Dict[str, Any]:
        """Get key metrics for investors"""
        if not self.use_database:
            return self._get_json_metrics()
        
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    metrics = {}
                    
                    # Total users
                    cur.execute("SELECT COUNT(*) FROM telegram_users")
                    metrics['total_users'] = cur.fetchone()[0]
                    
                    # Active subscribers
                    cur.execute("SELECT COUNT(*) FROM telegram_subscriptions WHERE status = 'active'")
                    metrics['active_subscribers'] = cur.fetchone()[0]
                    
                    # Active trials
                    cur.execute("SELECT COUNT(*) FROM telegram_trials WHERE status = 'active' AND trial_end > CURRENT_TIMESTAMP")
                    metrics['active_trials'] = cur.fetchone()[0]
                    
                    # Conversions (trial to paid)
                    cur.execute("SELECT COUNT(*) FROM telegram_trials WHERE converted_to_paid = true")
                    metrics['total_conversions'] = cur.fetchone()[0]
                    
                    # MRR
                    cur.execute("SELECT COUNT(*) * 1100 FROM telegram_subscriptions WHERE status = 'active'")
                    metrics['mrr_cents'] = cur.fetchone()[0] or 0
                    metrics['mrr_dollars'] = metrics['mrr_cents'] / 100
                    
                    # Last 7 days metrics
                    cur.execute("""
                        SELECT 
                            SUM(new_users) as new_users_7d,
                            SUM(total_messages) as messages_7d,
                            SUM(conversions) as conversions_7d
                        FROM daily_metrics 
                        WHERE date >= CURRENT_DATE - INTERVAL '7 days'
                    """)
                    row = cur.fetchone()
                    metrics['new_users_7d'] = row[0] or 0
                    metrics['messages_7d'] = row[1] or 0
                    metrics['conversions_7d'] = row[2] or 0
                    
                    # Conversion rate
                    if metrics['total_users'] > 0:
                        metrics['conversion_rate'] = round(metrics['total_conversions'] / metrics['total_users'] * 100, 2)
                    else:
                        metrics['conversion_rate'] = 0
                    
                    return metrics
        except Exception as e:
            logging.error(f"Error getting metrics: {e}")
            return self._get_json_metrics()
    
    def _get_json_metrics(self) -> Dict[str, Any]:
        """Fallback: Get metrics from JSON files"""
        metrics = {
            'total_users': 0,
            'active_subscribers': 0,
            'active_trials': 0,
            'mrr_cents': 0,
            'mrr_dollars': 0,
            'source': 'json_fallback'
        }
        
        try:
            # Count users from sessions
            if os.path.exists(self.json_users_file):
                with open(self.json_users_file, 'r') as f:
                    users = json.load(f)
                    metrics['total_users'] = len(users)
            
            # Count subscribers
            if os.path.exists(self.json_subscribers_file):
                with open(self.json_subscribers_file, 'r') as f:
                    subs = json.load(f)
                    active = sum(1 for s in subs.values() if s.get('status') == 'active')
                    metrics['active_subscribers'] = active
                    metrics['mrr_cents'] = active * 1100
                    metrics['mrr_dollars'] = metrics['mrr_cents'] / 100
        except Exception as e:
            logging.error(f"Error getting JSON metrics: {e}")
        
        return metrics
    
    # ==================== DATA MIGRATION ====================
    
    def migrate_from_json(self) -> Dict[str, int]:
        """Migrate existing JSON data to PostgreSQL"""
        if not self.use_database:
            return {'error': 'Database not available'}
        
        results = {'users': 0, 'subscribers': 0, 'trials': 0}
        
        try:
            # Migrate users from user_sessions.json
            if os.path.exists(self.json_users_file):
                with open(self.json_users_file, 'r') as f:
                    users = json.load(f)
                
                with self._get_connection() as conn:
                    with conn.cursor() as cur:
                        for user_id, data in users.items():
                            try:
                                cur.execute("""
                                    INSERT INTO telegram_users 
                                    (user_id, first_name, country, role, total_messages)
                                    VALUES (%s, %s, %s, %s, %s)
                                    ON CONFLICT (user_id) DO NOTHING
                                """, (
                                    user_id,
                                    data.get('user_name'),
                                    data.get('country'),
                                    data.get('role'),
                                    len(data.get('conversation_history', []))
                                ))
                                results['users'] += 1
                            except Exception as e:
                                logging.warning(f"Error migrating user {user_id}: {e}")
                        conn.commit()
            
            # Migrate subscribers
            if os.path.exists(self.json_subscribers_file):
                with open(self.json_subscribers_file, 'r') as f:
                    subs = json.load(f)
                
                with self._get_connection() as conn:
                    with conn.cursor() as cur:
                        for email, data in subs.items():
                            try:
                                user_id = data.get('telegram_id', 'unknown')
                                
                                # Ensure user exists
                                cur.execute("""
                                    INSERT INTO telegram_users (user_id, status)
                                    VALUES (%s, 'active')
                                    ON CONFLICT (user_id) DO UPDATE SET status = 'active'
                                """, (user_id,))
                                
                                cur.execute("""
                                    INSERT INTO telegram_subscriptions 
                                    (user_id, email, paypal_subscription_id, plan_id, source, status)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (paypal_subscription_id) DO NOTHING
                                """, (
                                    user_id,
                                    email,
                                    data.get('paypal_subscription_id', f'migrated_{email}'),
                                    data.get('plan_id', 'unknown'),
                                    'json_migration',
                                    data.get('status', 'active')
                                ))
                                results['subscribers'] += 1
                            except Exception as e:
                                logging.warning(f"Error migrating subscriber {email}: {e}")
                        conn.commit()
            
            logging.info(f"✅ Migration complete: {results}")
            return results
            
        except Exception as e:
            logging.error(f"Migration error: {e}")
            return {'error': str(e)}


# Global instance
db = EspaluzDatabase()

# Convenience functions
def track_user(user_id: str, **kwargs) -> bool:
    return db.track_user(user_id, **kwargs)

def track_message(user_id: str, message_type: str = 'text') -> bool:
    return db.track_message(user_id, message_type)

def start_trial(user_id: str, trial_days: int = 14) -> bool:
    return db.start_trial(user_id, trial_days)

def record_subscription(user_id: str, email: str, subscription_id: str, plan_id: str, source: str = 'direct_id') -> bool:
    return db.record_subscription(user_id, email, subscription_id, plan_id, source)

def log_event(user_id: str, event_type: str, event_data: Dict = None) -> bool:
    return db.log_event(user_id, event_type, event_data)

def get_investor_metrics() -> Dict[str, Any]:
    return db.get_investor_metrics()

def migrate_from_json() -> Dict[str, int]:
    return db.migrate_from_json()
