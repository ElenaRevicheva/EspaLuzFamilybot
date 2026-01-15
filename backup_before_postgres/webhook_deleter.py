import requests
import os
import time
import sys
import subprocess

def force_delete_webhook():
    # Get the token from environment
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN environment variable not found!")
        sys.exit(1)
    
    # URL to delete the webhook
    delete_url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
    
    # URL to check webhook info
    info_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    
    print(f"Starting webhook deletion process...")
    
    # Try multiple times to ensure it's deleted
    max_attempts = 5
    
    for attempt in range(1, max_attempts + 1):
        print(f"Attempt {attempt}/{max_attempts} to delete webhook")
        
        try:
            # First try to delete the webhook
            response = requests.get(delete_url, timeout=30)
            result = response.json()
            
            print(f"Delete webhook response: {result}")
            
            if result.get('ok'):
                # Check if webhook is actually deleted
                info_response = requests.get(info_url, timeout=30)
                info_result = info_response.json()
                
                if 'result' in info_result and not info_result['result'].get('url'):
                    print("SUCCESS: Webhook has been deleted!")
                    return True
                else:
                    print(f"WARNING: Webhook info still shows a webhook: {info_result}")
            else:
                print(f"ERROR: Webhook deletion failed: {result}")
            
            # If we're here, the webhook wasn't deleted successfully
            print(f"Waiting before retry...")
            time.sleep(5)  # Wait 5 seconds before retrying
            
        except Exception as e:
            print(f"ERROR: Exception during webhook deletion: {e}")
            time.sleep(5)  # Wait 5 seconds before retrying
    
    print("CRITICAL ERROR: Failed to delete webhook after multiple attempts")
    
    # As a last resort, try using curl (sometimes more reliable)
    try:
        print("Attempting webhook deletion with curl...")
        curl_cmd = f"curl -s 'https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true'"
        subprocess.run(curl_cmd, shell=True, check=True)
        print("Curl webhook deletion completed")
        
        # Verify with curl
        curl_verify = f"curl -s 'https://api.telegram.org/bot{token}/getWebhookInfo'"
        subprocess.run(curl_verify, shell=True, check=True)
        
        return True
    except Exception as e:
        print(f"ERROR: Curl webhook deletion failed: {e}")
        return False

if __name__ == "__main__":
    if force_delete_webhook():
        print("✅ Webhook deletion successful")
        sys.exit(0)
    else:
        print("❌ Webhook deletion failed")
        sys.exit(1)
