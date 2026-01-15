import sys
import os
import requests
sys.path.insert(0, '/home/ubuntu/EspaLuzFamilybot')
os.chdir('/home/ubuntu/EspaLuzFamilybot')
from dotenv import load_dotenv
load_dotenv('/home/ubuntu/EspaLuzFamilybot/.env')

PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
PAYPAL_BASE_URL = 'https://api.paypal.com'

# Get token
response = requests.post(
    f'{PAYPAL_BASE_URL}/v1/oauth2/token',
    headers={'Accept': 'application/json'},
    data='grant_type=client_credentials',
    auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
)
access_token = response.json().get('access_token')

headers = {'Authorization': f'Bearer {access_token}', 'Accept': 'application/json'}

# Try to get all subscriptions for our plan using different endpoints
print('Trying to find ALL subscriptions...')

# Try catalog products API to get product subscriptions
catalog_url = f'{PAYPAL_BASE_URL}/v1/catalogs/products/PROD-3N398307LC167491X'
res = requests.get(catalog_url, headers=headers)
print(f'Product details: {res.status_code}')
if res.status_code == 200:
    print(res.json())

# Try billing plans API
plan_url = f'{PAYPAL_BASE_URL}/v1/billing/plans/P-38A73508FY163121MNCJXTYY'
res = requests.get(plan_url, headers=headers)
print(f'Plan details: {res.status_code}')
if res.status_code == 200:
    data = res.json()
    print(f'Plan name: {data.get(" name\)}')
 print(f'Plan status: {data.get(\status\)}')
 
# Try searching payments/orders API
from datetime import datetime, timedelta, timezone
end_date = datetime.now(timezone.utc)
start_date = end_date - timedelta(hours=2) # Last 2 hours only

payments_url = f'{PAYPAL_BASE_URL}/v2/payments/authorizations'
res = requests.get(payments_url, headers=headers)
print(f'Payments API: {res.status_code}')

# Try partner referrals
partner_url = f'{PAYPAL_BASE_URL}/v2/customer/partner-referrals'
res = requests.get(partner_url, headers=headers)
print(f'Partner API: {res.status_code}')
