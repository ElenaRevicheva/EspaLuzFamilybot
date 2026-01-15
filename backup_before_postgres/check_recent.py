import os
import requests
from dotenv import load_dotenv
load_dotenv('/home/ubuntu/EspaLuzFamilybot/.env')

PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')

response = requests.post(
    'https://api.paypal.com/v1/oauth2/token',
    headers={'Accept': 'application/json'},
    data='grant_type=client_credentials',
    auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
)
access_token = response.json().get('access_token')
headers = {'Authorization': f'Bearer {access_token}', 'Accept': 'application/json'}

from datetime import datetime, timedelta, timezone
end_date = datetime.now(timezone.utc) - timedelta(hours=3)  # 3 hours ago
start_date = end_date - timedelta(days=7)

url = 'https://api.paypal.com/v1/reporting/transactions'
params = {
    'start_date': start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
    'end_date': end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
    'fields': 'all',
    'page_size': 500
}

res = requests.get(url, headers=headers, params=params, timeout=30)
if res.status_code == 200:
    txns = res.json().get('transaction_details', [])
    print(f'Found {len(txns)} transactions')
    for t in txns:
        email = t.get('payer_info', {}).get('email_address', '')
        ref = t.get('transaction_info', {}).get('paypal_reference_id', '')
        if 'elena' in email.lower() or 'revicheva' in email.lower():
            print(f'ELENA FOUND: {email}: {ref}')
        else:
            print(f'  {email}: {ref}')
else:
    print(f'Error: {res.status_code} - {res.text[:200]}')
