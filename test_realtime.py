import sys
import os
sys.path.insert(0, '/home/ubuntu/EspaLuzFamilybot')
os.chdir('/home/ubuntu/EspaLuzFamilybot')
from dotenv import load_dotenv
load_dotenv('/home/ubuntu/EspaLuzFamilybot/.env')

from espaluz_paypal_system import paypal_system
import os, sys
EMAIL = sys.argv[1] if len(sys.argv) > 1 else os.getenv('TEST_SUBSCRIBER_EMAIL', '')

print(f'Testing REAL-TIME subscription finder for {EMAIL}')
print('=' * 60)

result = paypal_system.find_subscription_for_email_realtime(EMAIL)
print(f'Result: {result}')
