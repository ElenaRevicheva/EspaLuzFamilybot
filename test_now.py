from espaluz_paypal_system import paypal_system, PAYPAL_BASE_URL, ESPALUZ_PLAN_ID
import requests

token = paypal_system.get_paypal_access_token()
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

# List ALL subscriptions without filtering
url = f'{PAYPAL_BASE_URL}/v1/billing/subscriptions'
res = requests.get(url, headers=headers, timeout=30)

print('Status:', res.status_code)
print('Response:', res.text[:1500])
