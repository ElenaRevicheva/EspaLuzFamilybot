#!/usr/bin/env python3
"""
EspaLuz Telegram PayPal Integration System
Ported and adapted from WhatsApp implementation
"""

import os
import json
import requests
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# PayPal Configuration
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")
PAYPAL_BASE_URL = "https://api.paypal.com"
ESPALUZ_PLAN_ID = "P-38A73508FY163121MNCJXTYY"
PAYPAL_SUBSCRIPTION_LINK = f"https://www.paypal.com/webapps/billing/plans/subscribe?plan_id={ESPALUZ_PLAN_ID}"

# Trial Configuration
DEFAULT_TRIAL_DAYS = 14  # 14-day free trial
ORG_TRIAL_DAYS = 60  # 60-day trial for organization members

# Data files
SUBSCRIBERS_FILE = "telegram_subscribers.json"
TRIALS_FILE = "telegram_trials.json"
PHONE_EMAIL_MAPPING_FILE = "telegram_phone_email_mapping.json"


class TelegramPayPalSystem:
    """Manages PayPal subscriptions and trials for Telegram bot"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(__file__)
        self.subscribers_file = os.path.join(self.base_dir, SUBSCRIBERS_FILE)
        self.trials_file = os.path.join(self.base_dir, TRIALS_FILE)
        self.mapping_file = os.path.join(self.base_dir, PHONE_EMAIL_MAPPING_FILE)
        
        # Initialize files if they don't exist
        self._ensure_files()
    
    def _ensure_files(self):
        """Ensure data files exist"""
        for filepath in [self.subscribers_file, self.trials_file, self.mapping_file]:
            if not os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    json.dump({}, f, indent=2)
    
    def _load_json(self, filepath: str) -> Dict:
        """Load JSON file safely"""
        try:
            with open(filepath, 'r') as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json(self, filepath: str, data: Dict):
        """Save JSON file"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    # ==================== PAYPAL API ====================
    
    def get_paypal_access_token(self) -> Optional[str]:
        """Get PayPal OAuth access token"""
        try:
            if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
                logging.warning("⚠️ PayPal credentials not configured")
                return None
            
            auth_url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"
            headers = {
                "Accept": "application/json",
                "Accept-Language": "en_US",
            }
            data = "grant_type=client_credentials"
            
            response = requests.post(
                auth_url,
                headers=headers,
                data=data,
                auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                logging.error(f"❌ Failed to get PayPal token: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"❌ PayPal token error: {e}")
            return None
    
    def check_paypal_subscription(self, email: str) -> Dict[str, Any]:
        """Check if email has active PayPal subscription"""
        try:
            # First check local subscribers
            subscribers = self._load_json(self.subscribers_file)
            email_lower = email.lower()
            
            if email_lower in subscribers:
                sub_data = subscribers[email_lower]
                if sub_data.get("status") == "active":
                    return {
                        "is_active": True,
                        "source": "local",
                        "subscription_id": sub_data.get("paypal_subscription_id"),
                        "email": email_lower
                    }
            
            # Then check PayPal API if credentials available
            access_token = self.get_paypal_access_token()
            if not access_token:
                return {"is_active": False, "reason": "no_paypal_credentials"}
            
            # For now, we rely on webhook + email linking
            # Direct API check would require subscription ID
            return {"is_active": False, "reason": "not_found"}
            
        except Exception as e:
            logging.error(f"❌ PayPal check error: {e}")
            return {"is_active": False, "reason": str(e)}
    
    # ==================== TRIAL SYSTEM ====================
    
    def start_trial(self, user_id: str, org_code: str = None) -> Dict[str, Any]:
        """Start a free trial for a user"""
        trials = self._load_json(self.trials_file)
        user_id_str = str(user_id)
        
        # Check if user already has a trial
        if user_id_str in trials:
            return trials[user_id_str]
        
        # Determine trial duration based on org code
        trial_days = ORG_TRIAL_DAYS if org_code else DEFAULT_TRIAL_DAYS
        
        trial_start = datetime.now()
        trial_end = trial_start + timedelta(days=trial_days)
        
        trial_data = {
            "user_id": user_id_str,
            "trial_start": trial_start.isoformat(),
            "trial_end": trial_end.isoformat(),
            "status": "active",
            "messages_sent": 0,
            "org_code": org_code,
            "created_at": trial_start.isoformat()
        }
        
        trials[user_id_str] = trial_data
        self._save_json(self.trials_file, trials)
        
        logging.info(f"✅ Started {trial_days}-day trial for user {user_id}")
        return trial_data
    
    def get_trial_status(self, user_id: str) -> Dict[str, Any]:
        """Get trial status for a user"""
        trials = self._load_json(self.trials_file)
        user_id_str = str(user_id)
        
        if user_id_str not in trials:
            return {
                "has_trial": False,
                "is_active": False,
                "days_remaining": 0,
                "status": "no_trial"
            }
        
        trial_data = trials[user_id_str]
        trial_end = datetime.fromisoformat(trial_data["trial_end"])
        now = datetime.now()
        
        days_remaining = max(0, (trial_end - now).days)
        hours_remaining = max(0, (trial_end - now).total_seconds() / 3600)
        is_active = now < trial_end and trial_data.get("status") == "active"
        
        return {
            "has_trial": True,
            "is_active": is_active,
            "days_remaining": days_remaining,
            "hours_remaining": hours_remaining,
            "trial_end": trial_data["trial_end"],
            "messages_sent": trial_data.get("messages_sent", 0),
            "org_code": trial_data.get("org_code"),
            "status": "active" if is_active else "expired"
        }
    
    def increment_message_count(self, user_id: str):
        """Increment message count for a user"""
        trials = self._load_json(self.trials_file)
        user_id_str = str(user_id)
        
        if user_id_str in trials:
            trials[user_id_str]["messages_sent"] = trials[user_id_str].get("messages_sent", 0) + 1
            self._save_json(self.trials_file, trials)
    
    def extend_trial(self, user_id: str, extra_days: int = 7) -> bool:
        """Extend a user's trial (admin function)"""
        trials = self._load_json(self.trials_file)
        user_id_str = str(user_id)
        
        if user_id_str not in trials:
            return False
        
        current_end = datetime.fromisoformat(trials[user_id_str]["trial_end"])
        new_end = current_end + timedelta(days=extra_days)
        
        trials[user_id_str]["trial_end"] = new_end.isoformat()
        trials[user_id_str]["status"] = "active"
        self._save_json(self.trials_file, trials)
        
        logging.info(f"✅ Extended trial for {user_id} by {extra_days} days")
        return True
    
    # ==================== SUBSCRIPTION CHECK ====================
    
    def is_user_allowed(self, user_id: str) -> Dict[str, Any]:
        """Check if user is allowed to use the bot (subscription or trial)"""
        user_id_str = str(user_id)
        
        # 1. Check if user has active subscription
        subscription = self._check_user_subscription(user_id_str)
        if subscription.get("is_active"):
            return {
                "allowed": True,
                "reason": "subscription",
                "message": "✅ Active subscription"
            }
        
        # 2. Check trial status
        trial_status = self.get_trial_status(user_id_str)
        
        if not trial_status["has_trial"]:
            # New user - start trial automatically
            self.start_trial(user_id_str)
            return {
                "allowed": True,
                "reason": "new_trial",
                "message": f"🎉 Welcome! You have a {DEFAULT_TRIAL_DAYS}-day free trial!",
            }
        
        if trial_status["is_active"]:
            days_left = trial_status["days_remaining"]
            if days_left > 1:
                message = f"✅ Trial active - {days_left} days remaining"
            else:
                hours_left = int(trial_status["hours_remaining"])
                message = f"⏰ Trial active - {hours_left} hours remaining"
            
            return {
                "allowed": True,
                "reason": "trial",
                "message": message
            }
        
        # Trial expired
        return {
            "allowed": False,
            "reason": "trial_expired",
            "message": self.get_subscription_prompt()
        }
    
    def _check_user_subscription(self, user_id: str) -> Dict[str, Any]:
        """Check if user has active subscription via email linking"""
        # Check phone-email mapping
        mappings = self._load_json(self.mapping_file)
        
        if user_id in mappings:
            email = mappings[user_id].get("email", "").lower()
            subscribers = self._load_json(self.subscribers_file)
            
            if email in subscribers and subscribers[email].get("status") == "active":
                return {"is_active": True, "email": email}
        
        # Check direct telegram_id in subscribers
        subscribers = self._load_json(self.subscribers_file)
        for email, data in subscribers.items():
            if str(data.get("telegram_id")) == str(user_id) and data.get("status") == "active":
                return {"is_active": True, "email": email}
        
        return {"is_active": False}
    
    # ==================== EMAIL LINKING ====================
    
    def is_email_pattern(self, text: str) -> bool:
        """Check if text looks like an email address"""
        text = text.strip()
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, text) is not None
    
    def link_email(self, user_id: str, email: str) -> Dict[str, Any]:
        """Link email to Telegram user for subscription verification"""
        user_id_str = str(user_id)
        email_lower = email.strip().lower()
        
        # Check if email has active PayPal subscription
        paypal_result = self.check_paypal_subscription(email_lower)
        
        if paypal_result.get("is_active"):
            # Link email to user
            self._store_email_mapping(user_id_str, email_lower)
            
            # Update subscriber with telegram_id
            subscribers = self._load_json(self.subscribers_file)
            if email_lower in subscribers:
                subscribers[email_lower]["telegram_id"] = user_id_str
                subscribers[email_lower]["linked_at"] = datetime.now().isoformat()
                self._save_json(self.subscribers_file, subscribers)
            
            return {
                "success": True,
                "message": """✅ ¡Email vinculado exitosamente!
✅ Email linked successfully!

🔵 PayPal subscription detected! You now have full access to EspaLuz.

🎉 ¡Ahora tienes acceso completo! Continúa tu viaje de aprendizaje."""
            }
        
        # Email not found - provide subscription link
        return {
            "success": False,
            "message": f"""⚠️ Email no encontrado / Email not found

No encontramos una suscripción activa para: {email}

Para suscribirte / To subscribe:
💳 PayPal: {PAYPAL_SUBSCRIPTION_LINK}

Después de suscribirte, envía tu email de PayPal aquí.
After subscribing, send your PayPal email here."""
        }
    
    def _store_email_mapping(self, user_id: str, email: str):
        """Store user_id -> email mapping"""
        mappings = self._load_json(self.mapping_file)
        mappings[user_id] = {
            "email": email,
            "linked_at": datetime.now().isoformat()
        }
        self._save_json(self.mapping_file, mappings)
    
    # ==================== MESSAGES ====================
    
    def get_subscription_prompt(self) -> str:
        """Get subscription prompt message"""
        return f"""🔐 Tu periodo de prueba ha expirado.
🔐 Your free trial has expired.

Para continuar usando EspaLuz, suscríbete:
To continue using EspaLuz, subscribe:

💳 **PayPal** ($15/mes - $15/month)
👉 {PAYPAL_SUBSCRIPTION_LINK}

📧 Después de suscribirte, envíame tu email de PayPal para activar tu acceso.
📧 After subscribing, send me your PayPal email to activate access.

✨ ¡No abandones tu viaje de aprendizaje!
✨ Don't give up on your learning journey!"""
    
    def get_trial_reminder(self, user_id: str) -> Optional[str]:
        """Get reminder message for users approaching trial end"""
        trial_status = self.get_trial_status(user_id)
        
        if not trial_status["is_active"]:
            return None
        
        days_left = trial_status["days_remaining"]
        hours_left = trial_status["hours_remaining"]
        
        if days_left <= 1 and hours_left <= 24:
            return f"""⏰ **Recordatorio de prueba / Trial Reminder**

Tu prueba gratis expira en {int(hours_left)} horas.
Your free trial expires in {int(hours_left)} hours.

No pierdas acceso a tu tutor de IA. Suscríbete ahora:
Don't lose access to your AI tutor. Subscribe now:

💳 PayPal: {PAYPAL_SUBSCRIPTION_LINK}

📧 After subscribing, send me your PayPal email."""
        
        elif days_left <= 2:
            return f"""📅 **Actualización de prueba / Trial Update**

¡{days_left} días restantes en tu prueba gratis!
{days_left} days left in your free trial!

¿Listo para continuar? / Ready to continue?
💳 PayPal: {PAYPAL_SUBSCRIPTION_LINK}"""
        
        return None
    
    # ==================== ADMIN FUNCTIONS ====================
    
    def get_all_trials(self) -> Dict[str, Any]:
        """Get all trial users"""
        return self._load_json(self.trials_file)
    
    def get_all_subscribers(self) -> Dict[str, Any]:
        """Get all subscribers"""
        return self._load_json(self.subscribers_file)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        trials = self._load_json(self.trials_file)
        subscribers = self._load_json(self.subscribers_file)
        
        now = datetime.now()
        active_trials = 0
        expired_trials = 0
        active_subscriptions = 0
        
        for user_id, data in trials.items():
            trial_end = datetime.fromisoformat(data["trial_end"])
            if now < trial_end and data.get("status") == "active":
                active_trials += 1
            else:
                expired_trials += 1
        
        for email, data in subscribers.items():
            if data.get("status") == "active":
                active_subscriptions += 1
        
        return {
            "total_trials": len(trials),
            "active_trials": active_trials,
            "expired_trials": expired_trials,
            "total_subscribers": len(subscribers),
            "active_subscriptions": active_subscriptions,
            "total_users": len(trials) + len(subscribers)
        }
    
    def add_subscriber_manually(self, email: str, paypal_subscription_id: str = None) -> bool:
        """Manually add a subscriber (for admin use)"""
        subscribers = self._load_json(self.subscribers_file)
        email_lower = email.lower()
        
        subscribers[email_lower] = {
            "status": "active",
            "source": "manual",
            "paypal_subscription_id": paypal_subscription_id,
            "telegram_id": None,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        self._save_json(self.subscribers_file, subscribers)
        logging.info(f"✅ Manually added subscriber: {email}")
        return True


# Global instance
paypal_system = TelegramPayPalSystem()
