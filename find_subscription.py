import os
import requests
import json
from dotenv import load_dotenv
load_dotenv('/home/ubuntu/EspaLuzFamilybot/.env')

PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
PAYPAL_BASE_URL = 'https://api.paypal.com'
ESPALUZ_PLAN_ID = 'P-38A73508FY163121MNCJXTYY'

# Get access token
auth_url = f'{PAYPAL_BASE_URL}/v1/oauth2/token'
response = requests.post(
    auth_url,
    headers={'Accept': 'application/json'},
    data='grant_type=client_credentials',
    auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
)
access_token = response.json().get('access_token')
print(f'Got access token: {access_token[:20]}...')

headers = {
    'Authorization': f'Bearer {access_token}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Try to get plan's subscriptions (not direct API but let's try)
print(f'\\nSearching for subscriptions to plan {ESPALUZ_PLAN_ID}...')

# Try transactions API
from datetime import datetime, timedelta, timezone
end_date = datetime.now(timezone.utc)
start_date = end_date - timedelta(days=7)

transactions_url = f'{PAYPAL_BASE_URL}/v1/reporting/transactions'
params = {
    'start_date': start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
    'end_date': end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
    'fields': 'all',
    'page_size': 100
}

print(f'Searching transactions from {start_date} to {end_date}...')
res = requests.get(transactions_url, headers=headers, params=params, timeout=15)
print(f'Transactions API response: {res.status_code}')

if res.status_code == 200:
    data = res.json()
    transactions = data.get('transaction_details', [])
    print(f'Found {len(transactions)} transactions')
    
    for txn in transactions:
        txn_info = txn.get('transaction_info', {})
        payer_info = txn.get('payer_info', {})
        payer_email = payer_info.get('email_address', '')
        txn_id = txn_info.get('transaction_id', '')
        paypal_ref = txn_info.get('paypal_reference_id', '')
        
        print(f'  - {payer_email}: txn={txn_id}, ref={paypal_ref}')
else:
    print(f'Error: {res.text[:500]}')

# Try to get subscription directly from known transaction
print('\\nTrying to look up subscription from transaction 4WM69069DH393160Y...')
capture_url = f'{PAYPAL_BASE_URL}/v2/payments/captures/4WM69069DH393160Y'
res = requests.get(capture_url, headers=headers, timeout=10)
print(f'Capture lookup: {res.status_code}')
if res.status_code == 200:
    print(json.dumps(res.json(), indent=2))
else:
    print(f'Error: {res.text[:300]}')
