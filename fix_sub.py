import subprocess
sql = """
INSERT INTO telegram_subscriptions (user_id, email, paypal_subscription_id, plan_id, status, source, started_at) 
VALUES ('5481526862', 'marinakulaginabowen@gmail.com', 'I-4JF9MBXLXM51', 'P-6GR95409C95293139NFSBJJY', 'active', 'paypal', NOW()) 
ON CONFLICT DO NOTHING;
UPDATE telegram_users SET status='subscriber' WHERE user_id='5481526862';
"""
result = subprocess.run(['sudo', '-u', 'postgres', 'psql', '-d', 'espaluz_telegram', '-c', sql], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)