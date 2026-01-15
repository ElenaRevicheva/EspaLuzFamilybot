#!/usr/bin/env python3
"""
PayPal Webhook Server - Receives REAL-TIME subscription notifications
Runs alongside the Telegram bot to capture new subscriptions INSTANTLY
No manual adding, no searching history - REAL webhooks!
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Use relative paths for portability
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SUBSCRIBERS_FILE = os.path.join(BASE_DIR, 'telegram_subscribers.json')
DISCOVERED_SUBS_FILE = os.path.join(BASE_DIR, 'discovered_subscription_ids.json')


def save_subscriber(email, subscription_id, status='active'):
    """Save subscriber to JSON file for the bot to use - REAL-TIME"""
    try:
        subscribers = {}
        if os.path.exists(SUBSCRIBERS_FILE):
            with open(SUBSCRIBERS_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    subscribers = json.loads(content)
        
        email_lower = email.lower()
        subscribers[email_lower] = {
            'status': status,
            'paypal_subscription_id': subscription_id,
            'source': 'paypal_webhook_realtime',
            'verified_at': datetime.now().isoformat(),
            'telegram_id': None
        }
        
        with open(SUBSCRIBERS_FILE, 'w') as f:
            json.dump(subscribers, f, indent=2)
        
        logging.info(f'WEBHOOK: Saved subscriber {email_lower} with subscription {subscription_id}')
        return True
    except Exception as e:
        logging.error(f'Error saving subscriber: {e}')
        return False


def save_discovered_subscription_id(subscription_id, email):
    """Save subscription ID for future lookups"""
    try:
        data = {'subscription_ids': [], 'details': {}}
        if os.path.exists(DISCOVERED_SUBS_FILE):
            with open(DISCOVERED_SUBS_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
        
        if subscription_id not in data['subscription_ids']:
            data['subscription_ids'].append(subscription_id)
            data['details'][subscription_id] = {
                'email': email,
                'discovered_at': datetime.now().isoformat(),
                'source': 'webhook'
            }
            
            with open(DISCOVERED_SUBS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            
            logging.info(f'WEBHOOK: Discovered new subscription ID {subscription_id}')
        return True
    except Exception as e:
        logging.error(f'Error saving subscription ID: {e}')
        return False


@app.route('/paypal-webhook', methods=['POST'])
def paypal_webhook():
    """Handle PayPal webhook notifications - REAL-TIME subscription events"""
    try:
        webhook_data = request.get_json() or {}
        event_type = webhook_data.get('event_type', '')
        resource = webhook_data.get('resource', {})
        
        logging.info(f'WEBHOOK RECEIVED: {event_type}')
        logging.info(f'Resource data: {str(resource)[:500]}')
        
        # Extract subscription info
        subscription_id = resource.get('id', '')
        subscriber = resource.get('subscriber', {})
        email = subscriber.get('email_address', '')
        status = resource.get('status', '').upper()
        
        # Handle subscription created/activated
        if event_type in ['BILLING.SUBSCRIPTION.CREATED', 'BILLING.SUBSCRIPTION.ACTIVATED']:
            if email and subscription_id:
                logging.info(f'NEW SUBSCRIPTION: {email} -> {subscription_id}')
                save_subscriber(email, subscription_id, 'active')
                save_discovered_subscription_id(subscription_id, email)
                return jsonify({'status': 'success', 'message': 'Subscription saved'}), 200
        
        # Handle subscription cancelled
        elif event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
            if email:
                logging.info(f'CANCELLED: {email}')
                save_subscriber(email, subscription_id, 'cancelled')
                return jsonify({'status': 'success'}), 200
        
        # Handle subscription suspended
        elif event_type == 'BILLING.SUBSCRIPTION.SUSPENDED':
            if email:
                logging.info(f'SUSPENDED: {email}')
                save_subscriber(email, subscription_id, 'suspended')
                return jsonify({'status': 'success'}), 200
        
        # Handle payment completed - extracts subscription from sale
        elif event_type == 'PAYMENT.SALE.COMPLETED':
            billing_agreement_id = resource.get('billing_agreement_id', '')
            payer = resource.get('payer', {}).get('payer_info', {})
            payer_email = payer.get('email', '') or payer.get('email_address', '')
            
            if billing_agreement_id and payer_email:
                logging.info(f'PAYMENT: {payer_email} -> {billing_agreement_id}')
                save_subscriber(payer_email, billing_agreement_id, 'active')
                save_discovered_subscription_id(billing_agreement_id, payer_email)
                return jsonify({'status': 'success'}), 200
        
        logging.info(f'Event logged: {event_type}')
        return jsonify({'status': 'received'}), 200
        
    except Exception as e:
        logging.error(f'Webhook error: {e}')
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'EspaLuz PayPal Webhook',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/', methods=['GET'])
def home():
    return 'EspaLuz PayPal Webhook Server - Running', 200


if __name__ == '__main__':
    logging.info('Starting PayPal Webhook Server on port 5000...')
    app.run(host='0.0.0.0', port=5000, debug=False)
