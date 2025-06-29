# 📞 Phone Call Alert Setup Guide

This guide will help you set up phone call alerts for HawkEye's live video stream monitoring.

## 🔧 Prerequisites

1. **Twilio Account**: Sign up at [twilio.com](https://www.twilio.com)
2. **Google Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. **Phone Number**: A phone number to receive alerts

## 📋 Step-by-Step Setup

### 1. Create Twilio Account
1. Go to [twilio.com](https://www.twilio.com) and sign up
2. Verify your account (you'll need a phone number for verification)
3. Get your Account SID and Auth Token from the Twilio Console

### 2. Get a Twilio Phone Number
1. In Twilio Console, go to "Phone Numbers" → "Manage" → "Buy a number"
2. Buy a phone number (this will be the "from" number for alerts)
3. Note down the phone number

### 3. Get Google Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the API key

### 4. Create Environment File
Create a file named `.env` in the HawkEye directory with the following content:

```env
# Google Gemini API (Required for AI analysis)
GOOGLE_API_KEY=your-actual-gemini-api-key

# Email Configuration (Required for email alerts)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Twilio Configuration (Required for phone call alerts)
TWILIO_ACCOUNT_SID=your-actual-twilio-account-sid
TWILIO_AUTH_TOKEN=your-actual-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890
ALERT_PHONE_NUMBER=+1234567890

# External Alarm System (Optional)
ALARM_SYSTEM_URL=https://your-alarm-system.com
ALARM_API_KEY=your-alarm-api-key

# Data Retention (Optional)
DATA_RETENTION_DAYS=30
```

### 5. Replace Placeholder Values

Replace the placeholder values in your `.env` file:

- `your-actual-gemini-api-key-here` → Your Google Gemini API key
- `your-actual-twilio-account-sid` → Your Twilio Account SID
- `your-actual-twilio-auth-token` → Your Twilio Auth Token
- `+1234567890` (TWILIO_PHONE_NUMBER) → Your Twilio phone number
- `+1234567890` (ALERT_PHONE_NUMBER) → Your personal phone number for receiving alerts

## 🧪 Testing the Setup

### 1. Test Configuration
Run the application and check the logs. You should see:

```
=== Call Service Configuration ===
TWILIO_ACCOUNT_SID: ✓ Set
TWILIO_AUTH_TOKEN: ✓ Set
TWILIO_PHONE_NUMBER: ✓ Set
ALERT_PHONE_NUMBER: ✓ Set
GOOGLE_API_KEY: ✓ Set
✓ Call service initialized successfully
```

### 2. Test Live Camera
1. Start the HawkEye application
2. Go to "Live Camera Monitoring"
3. Select your camera and start monitoring
4. When a threat is detected, you should receive a phone call

## 🔍 Troubleshooting

### No Phone Calls Received

1. **Check Environment Variables**:
   - Make sure `.env` file exists in the HawkEye directory
   - Verify all Twilio variables are set correctly
   - Restart the application after changing `.env`

2. **Check Logs**:
   - Look for "=== Call Service Configuration ===" in logs
   - Check for any "✗ Missing" indicators
   - Look for "=== Making Alert Call ===" when threats are detected

3. **Common Issues**:
   - **Missing .env file**: Create the `.env` file in the HawkEye directory
   - **Wrong phone number format**: Use international format (+1234567890)
   - **Twilio account not verified**: Verify your Twilio account
   - **Insufficient Twilio credits**: Add credits to your Twilio account

### Debug Mode
The application now includes enhanced logging. Check the console output for:
- Call service configuration status
- Threat detection events
- Call initiation attempts
- Success/failure messages

## 📞 How Phone Calls Work

When a threat is detected in live video stream:

1. **Detection**: YOLOv8 detects suspicious activity
2. **Analysis**: Gemini AI analyzes the captured frame
3. **Threat Assessment**: System determines threat level
4. **Call Trigger**: If threat level is MEDIUM, HIGH, or CRITICAL:
   - AI generates guidance message
   - Twilio makes automated call
   - Call includes threat details and AI recommendations

## 💰 Cost Information

- **Twilio**: ~$0.01 per minute for calls
- **Google Gemini**: ~$0.001 per request
- **Typical monthly cost**: $5-20 depending on usage

## 🆘 Support

If you're still having issues:

1. Check the application logs for error messages
2. Verify your Twilio account has sufficient credits
3. Test with a simple threat detection scenario
4. Ensure your phone number can receive calls from unknown numbers

---

**Note**: Phone call alerts work for both uploaded video files and live camera streams. The same detection and alerting system is used for both. 