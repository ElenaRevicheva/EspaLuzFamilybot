#!/usr/bin/env python3
"""
PayPal webhook + PagueloFacil webhook — receives server-side payment notifications.

PayPal: /paypal-webhook
PagueloFacil: /paguelofacil-webhook (HTTPS via webhook.aideazz.xyz)
Runs alongside Telegram bot infra; nginx proxies the hostname to this Flask app (port 5000).
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


def _emit_paypal_event(action, email, subscription_id, paypal_event_type):
    """Fire-and-forget wiring event for PayPal activity"""
    try:
        from wiring_emitter import emit_event
        emit_event(action, {
            "email": email,
            "subscription_id": subscription_id,
            "paypal_event": paypal_event_type,
            "amount": 7.77,
            "timestamp": datetime.now().isoformat()
        })
    except Exception:
        pass  # Never crash the webhook handler


@app.route('/paguelofacil-webhook', methods=['GET', 'POST', 'HEAD'])
@app.route('/paguelofacil-webhook/', methods=['GET', 'POST', 'HEAD'])
def paguelofacil_webhook():
    """
    PagueloFacil notifies via POST per https://developers.paguelofacil.com/guias/enlace-de-pago
    ('Configuración de webhook'). Body is typically JSON: merchantDescriptor, codOper, status,
    totalPay, operationType (e.g. RECURRENT, AUTH_CAPTURE).

    One URL serves all EspaLuz charges (customers may pay after WhatsApp OR Telegram—we attribute
    in app logic via metadata / subscriber records).

    Configure in PagueloFacil (HTTPS): https://webhook.aideazz.xyz/paguelofacil-webhook

    GET/HEAD: simple probe for uptime / support sanity checks (not a secret channel).
    """
    if request.method in ('GET', 'HEAD'):
        payload = {
            "ok": True,
            "service": "espaluz-payments-webhook",
            "paguelofacil_post_path": "/paguelofacil-webhook",
            "note": "EspaLuz operates on WhatsApp and Telegram (two systemd apps); Paguelofacil uses this single centralized URL for payment notifications.",
        }
        if request.method == 'HEAD':
            return '', 200
        return jsonify(payload), 200

    raw = request.get_data(cache=True) or b""
    ctype = request.content_type or ""
    payload_json = None
    try:
        payload_json = json.loads(raw.decode(request.charset or "utf-8"))
        cod = payload_json.get("codOper") or payload_json.get("relatedTx") or "n/a"
        logging.info(
            "PAGUELOFACIL WEBHOOK ctype=%s codOper=%s status=%s op=%s",
            ctype,
            cod,
            payload_json.get("status"),
            payload_json.get("operationType") or payload_json.get("merchantDescriptor"),
        )
        logging.info("PAGUELOFACIL WEBHOOK body (trunc): %s", json.dumps(payload_json)[:4000])
    except Exception:
        logging.info("PAGUELOFACIL WEBHOOK (non-json or empty) ctype=%s raw=%s", ctype, repr(raw[:2000]))
        return jsonify({"status": "received"}), 200

    try:
        from espaluz_paguelofacil import process_webhook
        result = process_webhook(payload_json)
        logging.info("PAGUELOFACIL processed: %s", result)
        return jsonify({"status": "received", "result": result}), 200
    except Exception as exc:
        logging.error("PAGUELOFACIL handler error: %s", exc)
        return jsonify({"status": "received", "handler_error": str(exc)}), 200


@app.route('/paypal-webhook', methods=['POST'])
def paypal_webhook():
    """Handle PayPal webhook notifications - REAL-TIME subscription events (unchanged behavior)."""
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
                _emit_paypal_event("payment_received", email, subscription_id, event_type)
                return jsonify({'status': 'success', 'message': 'Subscription saved'}), 200

        # Handle subscription cancelled
        elif event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
            if email:
                logging.info(f'CANCELLED: {email}')
                save_subscriber(email, subscription_id, 'cancelled')
                _emit_paypal_event("subscription_cancelled", email, subscription_id, event_type)
                return jsonify({'status': 'success'}), 200

        # Handle subscription suspended
        elif event_type == 'BILLING.SUBSCRIPTION.SUSPENDED':
            if email:
                logging.info(f'SUSPENDED: {email}')
                save_subscriber(email, subscription_id, 'suspended')
                _emit_paypal_event("subscription_cancelled", email, subscription_id, event_type)
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
                _emit_paypal_event("payment_received", payer_email, billing_agreement_id, event_type)
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
        'service': 'EspaLuz payments webhooks (PayPal + PagueloFacil)',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/', methods=['GET'])
def home():
    return (
        'EspaLuz payments webhooks — PayPal /paypal-webhook — '
        'PagueloFacil POST /paguelofacil-webhook (centralized for WhatsApp + Telegram)',
        200,
    )


if __name__ == '__main__':
    logging.info('Starting PayPal Webhook Server on port 5000...')
    app.run(host='0.0.0.0', port=5000, debug=False)
