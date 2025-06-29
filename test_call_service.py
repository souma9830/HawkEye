#!/usr/bin/env python3
"""
Test script for HawkEye Call Service
This script tests if the call service is properly configured and can make calls.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Test if all required environment variables are set"""
    print("🔍 Testing Environment Variables")
    print("=" * 40)
    
    required_vars = {
        'TWILIO_ACCOUNT_SID': 'Twilio Account SID',
        'TWILIO_AUTH_TOKEN': 'Twilio Auth Token', 
        'TWILIO_PHONE_NUMBER': 'Twilio Phone Number',
        'ALERT_PHONE_NUMBER': 'Alert Phone Number',
        'GOOGLE_API_KEY': 'Google Gemini API Key'
    }
    
    all_set = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {description}: Set")
        else:
            print(f"❌ {description}: Missing")
            all_set = False
    
    return all_set

def test_call_service():
    """Test the call service initialization"""
    print("\n📞 Testing Call Service")
    print("=" * 40)
    
    try:
        from call_service import CallService
        
        # Initialize call service
        call_service = CallService()
        
        if call_service.client:
            print("✅ Call service initialized successfully")
            return call_service
        else:
            print("❌ Call service failed to initialize")
            return None
            
    except ImportError as e:
        print(f"❌ Failed to import call service: {e}")
        return None
    except Exception as e:
        print(f"❌ Error initializing call service: {e}")
        return None

def test_make_call(call_service):
    """Test making a call (optional)"""
    print("\n🎯 Test Call Function")
    print("=" * 40)
    
    if not call_service:
        print("❌ Call service not available")
        return False
    
    print("This will make a test call to verify the service works.")
    response = input("Do you want to make a test call? (y/n): ").lower().strip()
    
    if response == 'y':
        try:
            print("Making test call...")
            result = call_service.make_alert_call(
                threat_level="TEST",
                location="Test Location",
                summary="This is a test call to verify the call service is working.",
                analysis_data={"test": True}
            )
            
            if result:
                print("✅ Test call initiated successfully!")
                print("You should receive a call shortly.")
            else:
                print("❌ Test call failed")
                
        except Exception as e:
            print(f"❌ Error making test call: {e}")
    else:
        print("Skipping test call")

def main():
    print("🔍 HawkEye Call Service Test")
    print("=" * 50)
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    if not env_ok:
        print("\n❌ Environment variables not properly configured!")
        print("Please create a .env file with the required variables.")
        print("See CALL_SETUP_GUIDE.md for detailed instructions.")
        return
    
    # Test call service
    call_service = test_call_service()
    
    if call_service:
        print("\n✅ Call service is ready!")
        test_make_call(call_service)
    else:
        print("\n❌ Call service is not working properly")
        print("Check your Twilio credentials and try again.")

if __name__ == "__main__":
    main() 