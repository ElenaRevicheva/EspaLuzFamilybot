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

# Collect ALL known subscription IDs and check each one
all_sub_ids = [
    'I-JWYRCYFWHL1H', 'I-J8DH55UMM6NL', 'I-J2PHFSWNB95P', 'I-HHD6PWYLS02C',
    'I-J75NTVBASYVK', 'I-8N2TWJCD74XJ', 'I-W1XSRABWWBGY', 'I-8LT2VUP05DNF',
    'I-51MYMXG2R006', 'I-WG4R7FBU16JT', 'I-FN4W31PE8G07', 'I-N32S1EJG29S7',
    'I-YDTB45W0BP7U', 'I-1S4N27E64VKM', 'I-MJV7LMY3NRK8'
]

print(f'Checking {len(all_sub_ids)} subscription IDs...')
print()

active_by_email = {}

for sub_id in all_sub_ids:
    url = f'{PAYPAL_BASE_URL}/v1/billing/subscriptions/{sub_id}'
    res = requests.get(url, headers=headers, timeout=10)
    
    if res.status_code == 200:
        data = res.json()
        email = data.get('subscriber', {}).get('email_address', 'unknown')
        status = data.get('status', 'UNKNOWN')
        plan_id = data.get('plan_id', '')
        
        if status == 'ACTIVE' and plan_id == ESPALUZ_PLAN_ID:
            print(f'âœ… ACTIVE: {sub_id} -> {email}')
            active_by_email[email.lower()] = sub_id
        else:
            print(f'   {status}: {sub_id} -> {email} (plan: {plan_id})')
    else:
        print(f'âŒ NOT FOUND: {sub_id}')

print()
print('=' * 50)
print('ACTIVE SUBSCRIPTIONS BY EMAIL:')
for email, sub_id in active_by_email.items():
    print(f'  {email}: {sub_id}')
