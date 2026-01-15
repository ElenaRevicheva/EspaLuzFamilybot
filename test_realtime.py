import sys
import os
sys.path.insert(0, '/home/ubuntu/EspaLuzFamilybot')
os.chdir('/home/ubuntu/EspaLuzFamilybot')
from dotenv import load_dotenv
load_dotenv('/home/ubuntu/EspaLuzFamilybot/.env')

from espaluz_paypal_system import paypal_system

print('Testing REAL-TIME subscription finder for elena.revicheva2016@gmail.com')
print('=' * 60)

result = paypal_system.find_subscription_for_email_realtime('elena.revicheva2016@gmail.com')
print(f'Result: {result}')
