#!/usr/bin/env python3
"""
EspaLuz Telegram PayPal Integration System
Ported and adapted from WhatsApp implementation
"""

import os
from dotenv import load_dotenv
load_dotenv()  # Load .env before reading credentials
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
ESPALUZ_PLAN_ID = "P-6GR95409C95293139NFSBJJY"
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
        """Check if email has active PayPal subscription - REAL PayPal API verification"""
        try:
            email_lower = email.lower()
            
            # First check telegram_subscribers.json (already verified PayPal)
            subscribers = self._load_json(self.subscribers_file)
            if email_lower in subscribers:
                sub_data = subscribers[email_lower]
                if sub_data.get("status") == "active":
                    return {
                        "is_active": True,
                        "source": "paypal_verified",
                        "subscription_id": sub_data.get("paypal_subscription_id"),
                        "email": email_lower
                    }
            
            # REAL PayPal API verification - check known subscription IDs
            realtime_result = self._check_paypal_realtime(email_lower)
            if realtime_result and realtime_result.get("is_active"):
                # Store verified subscription for future use
                self._store_verified_subscriber(email_lower, realtime_result.get("subscription_id"))
                return realtime_result
            
            return {"is_active": False, "reason": "not_found_in_paypal"}
            
        except Exception as e:
            logging.error(f"❌ PayPal check error: {e}")
            return {"is_active": False, "reason": str(e)}
    
    def _check_paypal_realtime(self, email: str) -> Optional[Dict[str, Any]]:
        """REAL PayPal API verification - search transactions for NEW subscribers"""
        try:
            access_token = self.get_paypal_access_token()
            if not access_token:
                logging.warning("⚠️ PayPal credentials not available for real-time verification")
                return None
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # METHOD 1: Search recent transactions by email (last 31 days)
            logging.info(f"🔍 Searching PayPal transactions for {email}...")
            
            from datetime import timezone
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=31)
            
            transactions_url = f"{PAYPAL_BASE_URL}/v1/reporting/transactions"
            params = {
                "start_date": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_date": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "fields": "all",
                "page_size": 100
            }
            
            try:
                res = requests.get(transactions_url, headers=headers, params=params, timeout=15)
                
                if res.status_code == 200:
                    data = res.json()
                    transactions = data.get("transaction_details", [])
                    logging.info(f"📋 Found {len(transactions)} recent transactions")
                    
                    for txn in transactions:
                        txn_info = txn.get("transaction_info", {})
                        payer_info = txn.get("payer_info", {})
                        payer_email = payer_info.get("email_address", "").lower()
                        
                        if payer_email == email.lower():
                            # Found transaction for this email - get subscription ID
                            txn_event_code = txn_info.get("transaction_event_code", "")
                            billing_agreement_id = txn_info.get("paypal_reference_id", "")
                            
                            # T0002 = subscription payment
                            if "T0002" in txn_event_code or billing_agreement_id.startswith("I-"):
                                logging.info(f"✅ Found subscription transaction: {billing_agreement_id}")
                                
                                # Verify this subscription is active
                                if billing_agreement_id:
                                    sub_check = self._verify_subscription_id(headers, billing_agreement_id, email)
                                    if sub_check:
                                        return sub_check
                                        
            except Exception as e:
                logging.warning(f"⚠️ Transaction search failed: {e}")
            
            # METHOD 2: Check known subscription IDs (fallback for older subscribers)
            logging.info(f"🔍 Checking known subscription IDs for {email}...")
            known_subscription_ids = [
                "I-N32S1EJG29S7",  # Marina Kulagina
                "I-YDTB45W0BP7U",
                "I-1S4N27E64VKM",
                "I-MJV7LMY3NRK8",
            ]
            
            for subscription_id in known_subscription_ids:
                result = self._verify_subscription_id(headers, subscription_id, email)
                if result:
                    return result
            
            # METHOD 3: Search subscriptions for our plan directly
            logging.info(f"🔍 Searching all plan subscriptions for {email}...")
            result = self._search_plan_subscriptions(headers, email)
            if result:
                return result
            
            logging.info(f"❌ No active PayPal subscriptions found for {email}")
            return {"is_active": False, "reason": "no_matching_subscription"}
            
        except Exception as e:
            logging.error(f"❌ Error in PayPal real-time verification: {e}")
            return None
    
    def _verify_subscription_id(self, headers: dict, subscription_id: str, email: str) -> Optional[Dict[str, Any]]:
        """Verify a specific subscription ID belongs to the email and is active"""
        try:
            url = f"{PAYPAL_BASE_URL}/v1/billing/subscriptions/{subscription_id}"
            res = requests.get(url, headers=headers, timeout=10)
            
            if res.status_code == 200:
                sub_data = res.json()
                subscriber_email = sub_data.get('subscriber', {}).get('email_address', '').lower()
                
                if subscriber_email == email.lower():
                    status = sub_data.get('status', '').upper()
                    plan_id = sub_data.get('plan_id', '')
                    
                    if status in ['ACTIVE', 'APPROVED']:
                        logging.info(f"✅ VERIFIED: {subscription_id} for {email} is {status}")
                        return {
                            "is_active": True,
                            "source": "paypal_api_verified",
                            "subscription_id": subscription_id,
                            "status": status,
                            "plan_id": plan_id,
                            "email": email
                        }
            return None
        except Exception as e:
            logging.warning(f"⚠️ Error verifying {subscription_id}: {e}")
            return None
    
    def _search_plan_subscriptions(self, headers: dict, email: str) -> Optional[Dict[str, Any]]:
        """Search all subscriptions for our plan - finds NEW subscribers"""
        try:
            # Load dynamically discovered subscription IDs
            discovered_ids = self._load_discovered_subscription_ids()
            
            for sub_id in discovered_ids:
                result = self._verify_subscription_id(headers, sub_id, email)
                if result:
                    return result
            
            return None
        except Exception as e:
            logging.warning(f"⚠️ Plan subscription search failed: {e}")
            return None
    
    def _load_discovered_subscription_ids(self) -> list:
        """Load dynamically discovered subscription IDs"""
        try:
            filepath = os.path.join(self.base_dir, "discovered_subscription_ids.json")
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    return data.get("subscription_ids", [])
            return []
        except:
            return []
    
    def _save_discovered_subscription_id(self, subscription_id: str, email: str):
        """Save newly discovered subscription ID"""
        try:
            filepath = os.path.join(self.base_dir, "discovered_subscription_ids.json")
            data = {"subscription_ids": [], "details": {}}
            
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
            
            if subscription_id not in data["subscription_ids"]:
                data["subscription_ids"].append(subscription_id)
                data["details"][subscription_id] = {
                    "email": email,
                    "discovered_at": datetime.now().isoformat()
                }
                
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                
                logging.info(f"✅ Saved new subscription ID: {subscription_id} for {email}")
        except Exception as e:
            logging.error(f"❌ Error saving subscription ID: {e}")
    
    def lookup_subscription_from_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Look up subscription ID from a PayPal transaction ID (from IPN)"""
        try:
            access_token = self.get_paypal_access_token()
            if not access_token:
                return None
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            # Get transaction details
            url = f"{PAYPAL_BASE_URL}/v2/payments/captures/{transaction_id}"
            res = requests.get(url, headers=headers, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                # Look for billing agreement/subscription reference
                links = data.get("links", [])
                for link in links:
                    if "billing-agreement" in link.get("href", "") or "subscriptions" in link.get("href", ""):
                        # Extract subscription ID from link
                        href = link.get("href", "")
                        if "I-" in href:
                            sub_id = href.split("/")[-1]
                            logging.info(f"✅ Found subscription ID from transaction: {sub_id}")
                            return {"subscription_id": sub_id, "transaction_id": transaction_id}
            
            logging.warning(f"⚠️ Could not find subscription from transaction {transaction_id}")
            return None
            
        except Exception as e:
            logging.error(f"❌ Error looking up transaction: {e}")
            return None
    
    def add_subscription_manually(self, email: str, subscription_id: str) -> Dict[str, Any]:
        """Manually add a subscription ID for immediate verification (admin function)"""
        try:
            access_token = self.get_paypal_access_token()
            if not access_token:
                return {"success": False, "error": "No PayPal credentials"}
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            # Verify the subscription exists and is active
            url = f"{PAYPAL_BASE_URL}/v1/billing/subscriptions/{subscription_id}"
            res = requests.get(url, headers=headers, timeout=10)
            
            if res.status_code == 200:
                sub_data = res.json()
                subscriber_email = sub_data.get('subscriber', {}).get('email_address', '').lower()
                status = sub_data.get('status', '').upper()
                
                if status in ['ACTIVE', 'APPROVED']:
                    # Save to discovered IDs
                    self._save_discovered_subscription_id(subscription_id, subscriber_email)
                    
                    # Save to verified subscribers
                    self._store_verified_subscriber(subscriber_email, subscription_id)
                    
                    return {
                        "success": True,
                        "email": subscriber_email,
                        "subscription_id": subscription_id,
                        "status": status
                    }
                else:
                    return {"success": False, "error": f"Subscription status is {status}, not ACTIVE"}
            else:
                return {"success": False, "error": f"Subscription not found: {res.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _store_verified_subscriber(self, email: str, subscription_id: str):
        """Store verified subscriber for future lookups"""
        try:
            subscribers = self._load_json(self.subscribers_file)
            subscribers[email] = {
                "status": "active",
                "paypal_subscription_id": subscription_id,
                "source": "paypal_api_verified",
                "verified_at": datetime.now().isoformat(),
                "telegram_id": None
            }
            self._save_json(self.subscribers_file, subscribers)
            logging.info(f"✅ Stored verified subscriber: {email} with {subscription_id}")
        except Exception as e:
            logging.error(f"❌ Error storing verified subscriber: {e}")
    
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
        """Link email to Telegram user for subscription verification - REAL-TIME"""
        user_id_str = str(user_id)
        email_lower = email.strip().lower()
        
        logging.info(f"LINK EMAIL: Checking {email_lower} for user {user_id_str}")
        
        # FIRST: Try real-time search in PayPal (finds NEW subscribers!)
        realtime_result = self.find_subscription_for_email_realtime(email_lower)
        if realtime_result and realtime_result.get("is_active"):
            logging.info(f"FOUND via real-time search: {email_lower}")
            paypal_result = realtime_result
        else:
            # FALLBACK: Check local cache
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
        
        # Email not found - ask for subscription ID
        return {
            "success": False,
            "message": f"""⚠️ Email no encontrado / Email not found

No encontramos una suscripción activa para: {email}

🔑 Si ya te suscribiste, envía tu ID de suscripción:
   (Lo encuentras en PayPal → Configuración → Pagos → Pagos automáticos)
   Formato: I-XXXXXXXXXXXX

🆕 Si no tienes suscripción, suscríbete aquí:
💳 PayPal: {PAYPAL_SUBSCRIPTION_LINK}

If you already subscribed, send your Subscription ID (I-XXXXXXXXXXXX).
Find it in PayPal → Settings → Payments → Automatic payments."""
        }
    
    def verify_subscription_id_direct(self, user_id: str, subscription_id: str) -> Dict[str, Any]:
        """
        REAL-TIME verification of subscription ID via PayPal API.
        User provides their subscription ID (I-XXXX) and we verify it directly.
        NO simulation, NO manual adding - REAL PayPal API verification.
        """
        user_id_str = str(user_id)
        subscription_id = subscription_id.strip().upper()
        
        # Validate format
        if not subscription_id.startswith("I-") or len(subscription_id) < 10:
            return {
                "success": False,
                "message": "⚠️ Formato inválido. El ID debe empezar con I- (ejemplo: I-13BWRCW9G2K2)"
            }
        
        try:
            access_token = self.get_paypal_access_token()
            if not access_token:
                return {"success": False, "message": "⚠️ PayPal API no disponible. Intenta más tarde."}
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            # REAL PayPal API call to verify subscription
            url = f"{PAYPAL_BASE_URL}/v1/billing/subscriptions/{subscription_id}"
            res = requests.get(url, headers=headers, timeout=15)
            
            if res.status_code == 200:
                data = res.json()
                status = data.get("status", "").upper()
                subscriber_email = data.get("subscriber", {}).get("email_address", "").lower()
                plan_id = data.get("plan_id", "")
                
                if status == "ACTIVE":
                    # Save verified subscription
                    subscribers = self._load_json(self.subscribers_file)
                    subscribers[subscriber_email] = {
                        "status": "active",
                        "paypal_subscription_id": subscription_id,
                        "source": "direct_id_verification",
                        "verified_at": datetime.now().isoformat(),
                        "telegram_id": user_id_str,
                        "plan_id": plan_id
                    }
                    self._save_json(self.subscribers_file, subscribers)
                    
                    # Save mapping
                    self._store_email_mapping(user_id_str, subscriber_email)
                    
                    # Save subscription ID for future lookups
                    self._save_discovered_subscription_id(subscription_id, subscriber_email)
                    
                    return {
                        "success": True,
                        "message": f"""✅ ¡Suscripción verificada exitosamente!
✅ Subscription verified successfully!

📧 Email: {subscriber_email}
🔑 ID: {subscription_id}
✅ Status: ACTIVO

🎉 ¡Ahora tienes acceso completo a EspaLuz!
🎉 You now have full access to EspaLuz!"""
                    }
                else:
                    return {
                        "success": False,
                        "message": f"⚠️ Suscripción encontrada pero status es: {status}\nSubscription found but status is: {status}"
                    }
            
            elif res.status_code == 404:
                return {
                    "success": False,
                    "message": "❌ ID de suscripción no encontrado en PayPal.\n❌ Subscription ID not found in PayPal."
                }
            else:
                return {
                    "success": False,
                    "message": f"⚠️ Error verificando suscripción: {res.status_code}"
                }
                
        except Exception as e:
            logging.error(f"Error verifying subscription ID: {e}")
            return {"success": False, "message": f"⚠️ Error: {str(e)}"}
    
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

💳 **PayPal** ($11/mes - $11/month + 14-day FREE trial!)
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


    def find_subscription_for_email_realtime(self, email: str) -> Optional[Dict[str, Any]]:
        """
        REAL-TIME subscription finder - queries PayPal API directly for this email
        This is the PRIMARY method for finding NEW subscribers
        """
        try:
            access_token = self.get_paypal_access_token()
            if not access_token:
                logging.warning("No PayPal credentials available")
                return None
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            email_lower = email.lower()
            logging.info(f"REAL-TIME SEARCH: Looking for subscription for {email_lower}")
            
            # Method 1: Search recent transactions (last 31 days) for this email
            from datetime import timezone
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=31)
            
            transactions_url = f"{PAYPAL_BASE_URL}/v1/reporting/transactions"
            params = {
                "start_date": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_date": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "fields": "all",
                "page_size": 500
            }
            
            res = requests.get(transactions_url, headers=headers, params=params, timeout=30)
            
            if res.status_code == 200:
                data = res.json()
                transactions = data.get("transaction_details", [])
                
                for txn in transactions:
                    payer_info = txn.get("payer_info", {})
                    payer_email = payer_info.get("email_address", "").lower()
                    txn_info = txn.get("transaction_info", {})
                    paypal_ref = txn_info.get("paypal_reference_id", "")
                    
                    if payer_email == email_lower and paypal_ref.startswith("I-"):
                        # Found a subscription ID for this email!
                        logging.info(f"FOUND: {email_lower} -> {paypal_ref}")
                        
                        # Verify it's active
                        result = self._verify_subscription_id(headers, paypal_ref, email_lower)
                        if result and result.get("is_active"):
                            # Store it for future use
                            self._store_verified_subscriber(email_lower, paypal_ref)
                            self._save_discovered_subscription_id(paypal_ref, email_lower)
                            return result
            
            # Method 2: Check all known + discovered subscription IDs
            all_sub_ids = self._get_all_known_subscription_ids()
            
            for sub_id in all_sub_ids:
                result = self._verify_subscription_id(headers, sub_id, email_lower)
                if result and result.get("is_active"):
                    self._store_verified_subscriber(email_lower, sub_id)
                    return result
            
            logging.info(f"No active subscription found for {email_lower}")
            return None
            
        except Exception as e:
            logging.error(f"Error in real-time subscription search: {e}")
            return None
    
    def _get_all_known_subscription_ids(self) -> list:
        """Get all known subscription IDs from various sources"""
        all_ids = set()
        
        # 1. Hardcoded known IDs
        known_ids = [
            "I-N32S1EJG29S7", "I-JWYRCYFWHL1H", "I-J8DH55UMM6NL",
            "I-J2PHFSWNB95P", "I-HHD6PWYLS02C", "I-J75NTVBASYVK",
            "I-8N2TWJCD74XJ", "I-W1XSRABWWBGY", "I-8LT2VUP05DNF",
            "I-51MYMXG2R006", "I-WG4R7FBU16JT", "I-FN4W31PE8G07",
        ]
        all_ids.update(known_ids)
        
        # 2. Discovered IDs from file
        discovered = self._load_discovered_subscription_ids()
        all_ids.update(discovered)
        
        # 3. IDs from existing subscribers
        subscribers = self._load_json(self.subscribers_file)
        for email, data in subscribers.items():
            sub_id = data.get("paypal_subscription_id")
            if sub_id and sub_id.startswith("I-"):
                all_ids.add(sub_id)
        
        return list(all_ids)
    
    def poll_for_new_subscriptions(self) -> int:
        """
        Poll PayPal for new subscriptions - runs periodically
        Returns count of new subscriptions found
        """
        try:
            access_token = self.get_paypal_access_token()
            if not access_token:
                return 0
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            # Get recent transactions
            from datetime import timezone
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)
            
            transactions_url = f"{PAYPAL_BASE_URL}/v1/reporting/transactions"
            params = {
                "start_date": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_date": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "fields": "all",
                "page_size": 500
            }
            
            res = requests.get(transactions_url, headers=headers, params=params, timeout=30)
            
            if res.status_code != 200:
                return 0
            
            data = res.json()
            transactions = data.get("transaction_details", [])
            new_count = 0
            
            existing_subscribers = self._load_json(self.subscribers_file)
            
            for txn in transactions:
                payer_info = txn.get("payer_info", {})
                payer_email = payer_info.get("email_address", "").lower()
                txn_info = txn.get("transaction_info", {})
                paypal_ref = txn_info.get("paypal_reference_id", "")
                
                if paypal_ref.startswith("I-") and payer_email:
                    # Check if we already have this subscriber
                    if payer_email not in existing_subscribers:
                        # Verify and add
                        result = self._verify_subscription_id(headers, paypal_ref, payer_email)
                        if result and result.get("is_active"):
                            self._store_verified_subscriber(payer_email, paypal_ref)
                            self._save_discovered_subscription_id(paypal_ref, payer_email)
                            new_count += 1
                            logging.info(f"POLLER: Found new subscriber {payer_email}")
            
            return new_count
            
        except Exception as e:
            logging.error(f"Polling error: {e}")
            return 0


# Global instance
paypal_system = TelegramPayPalSystem()
