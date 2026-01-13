#!/usr/bin/env python3
"""Disable the Gumroad subscription poller thread"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_poller = '''def run_subscription_poller():
    from poll_subscriptions import fetch_all_subscribers, update_subscriber_file
    while True:
        try:
            print(f"\\n🔄 Polling Gumroad API inside bot runtime...")
            subscribers = fetch_all_subscribers()
            update_subscriber_file(subscribers)
        except Exception as e:
            print(f"❌ Subscription poller crashed: {e}")
        time.sleep(300)  # poll every 5 minutes

threading.Thread(target=run_subscription_poller, daemon=True).start()'''

new_poller = '''# DISABLED: Gumroad subscription poller - using PayPal now
# def run_subscription_poller():
#     from poll_subscriptions import fetch_all_subscribers, update_subscriber_file
#     while True:
#         try:
#             print(f"\\n🔄 Polling Gumroad API inside bot runtime...")
#             subscribers = fetch_all_subscribers()
#             update_subscriber_file(subscribers)
#         except Exception as e:
#             print(f"❌ Subscription poller crashed: {e}")
#         time.sleep(300)
# threading.Thread(target=run_subscription_poller, daemon=True).start()
print("📌 Gumroad poller disabled - using PayPal subscriptions")'''

if old_poller in content:
    content = content.replace(old_poller, new_poller)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: Disabled Gumroad subscription poller thread')
else:
    print('Pattern not found - checking current state...')
    # Show what's there
    if 'run_subscription_poller' in content:
        print('Function exists but pattern differs')
    else:
        print('Function not found')
