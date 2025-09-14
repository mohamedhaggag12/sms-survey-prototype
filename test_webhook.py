#!/usr/bin/env python3
"""
Test script to simulate TextBelt webhook calls for testing SMS response collection
"""

import requests
import json

# Test data simulating a TextBelt webhook payload
test_responses = [
    {
        "textId": "12345",
        "fromNumber": "+16172900797",  # Your phone number
        "text": "8 7 9 Had a really productive day at work and felt accomplished"
    },
    {
        "textId": "12346", 
        "fromNumber": "+16172900797",
        "text": "5 6 4 Feeling a bit down today, work was stressful"
    },
    {
        "textId": "12347",
        "fromNumber": "+16172900797", 
        "text": "10 9 8 Amazing day! Got promoted and spent time with family"
    }
]

def test_webhook(use_production=False):
    """Send test webhook calls to the Flask app"""
    if use_production:
        webhook_url = "https://sms-survey-prototype-production.up.railway.app/sms_webhook"
        print("🧪 Testing SMS webhook responses on PRODUCTION...")
    else:
        webhook_url = "http://127.0.0.1:5001/sms_webhook"
        print("🧪 Testing SMS webhook responses on LOCAL...")

    print("=" * 50)
    print(f"Target URL: {webhook_url}")
    
    for i, response_data in enumerate(test_responses, 1):
        print(f"\n📱 Test {i}: Sending response from {response_data['fromNumber']}")
        print(f"   Message: {response_data['text']}")
        
        try:
            # Send POST request to webhook endpoint
            result = requests.post(
                webhook_url,
                json=response_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if result.status_code == 200:
                print(f"   ✅ Webhook accepted (Status: {result.status_code})")
            else:
                print(f"   ❌ Webhook failed (Status: {result.status_code})")
                print(f"   Response: {result.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection failed - is the Flask app running on port 5001?")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 50)
    if use_production:
        print("🎯 Test complete! Check the responses page: https://sms-survey-prototype-production.up.railway.app/responses")
    else:
        print("🎯 Test complete! Check the responses page: http://127.0.0.1:5001/responses")

if __name__ == "__main__":
    import sys
    use_prod = len(sys.argv) > 1 and sys.argv[1] == "prod"
    test_webhook(use_production=use_prod)
