import sys
import os
import json
sys.path.insert(0, '/home/ubuntu/EspaLuzFamilybot')
os.chdir('/home/ubuntu/EspaLuzFamilybot')

# Load env manually
from dotenv import load_dotenv
load_dotenv('/home/ubuntu/EspaLuzFamilybot/.env')

from espaluz_paypal_system import paypal_system

# Clear to force real API check
with open('telegram_subscribers.json', 'w') as f:
    json.dump({}, f)

print('Cleared telegram_subscribers.json - forcing REAL PayPal API check...')

# Test
email = 'marinakulaginabowen@gmail.com'
print(f'Testing REAL PayPal API for: {email}')
result = paypal_system.check_paypal_subscription(email)
print(f'Result: {result}')

# Check stored
with open('telegram_subscribers.json', 'r') as f:
    stored = json.load(f)
print(f'Stored: {stored}')
