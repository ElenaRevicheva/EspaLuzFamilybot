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

headers = {
    'Authorization': f'Bearer {access_token}',
    'Accept': 'application/json',
}

# Search last 31 days of transactions
from datetime import datetime, timedelta, timezone
end_date = datetime.now(timezone.utc)
start_date = end_date - timedelta(days=31)

transactions_url = f'{PAYPAL_BASE_URL}/v1/reporting/transactions'
params = {
    'start_date': start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
    'end_date': end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
    'fields': 'all',
    'page_size': 500
}

print('Searching ALL recent transactions...')
res = requests.get(transactions_url, headers=headers, params=params, timeout=30)

if res.status_code == 200:
    data = res.json()
    transactions = data.get('transaction_details', [])
    print(f'Found {len(transactions)} transactions total')
    
    elena_found = False
    marina_subs = []
    
    for txn in transactions:
        txn_info = txn.get('transaction_info', {})
        payer_info = txn.get('payer_info', {})
        payer_email = payer_info.get('email_address', '').lower()
        paypal_ref = txn_info.get('paypal_reference_id', '')
        txn_id = txn_info.get('transaction_id', '')
        
        # Look for any subscription reference
        if paypal_ref.startswith('I-'):
            print(f'  SUBSCRIPTION: {payer_email} -> {paypal_ref} (txn: {txn_id})')
            
            if 'elena' in payer_email or 'revicheva' in payer_email:
                elena_found = True
                print(f'  >>> FOUND ELENA: {paypal_ref}')
            if 'marina' in payer_email:
                marina_subs.append(paypal_ref)
    
    print(f'\\nMarina subscriptions found: {marina_subs}')
    
    if not elena_found:
        print('\\nElena NOT found in transactions. Her subscription might be too new.')
        print('Checking if we can list ALL plan subscriptions...')
        
        # Try to get catalog/products
        catalog_url = f'{PAYPAL_BASE_URL}/v1/catalogs/products'
        res2 = requests.get(catalog_url, headers=headers)
        print(f'Catalog response: {res2.status_code}')
        if res2.status_code == 200:
            print(json.dumps(res2.json(), indent=2)[:1000])
else:
    print(f'Error: {res.status_code} - {res.text[:500]}')
