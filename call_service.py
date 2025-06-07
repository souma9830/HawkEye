from twilio.rest import Client
import os
from datetime import datetime
import logging
import openai
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CallService:
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.to_number = os.getenv('ALERT_PHONE_NUMBER')
        self.client = None
        
        # Initialize OpenAI
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        if all([self.account_sid, self.auth_token, self.from_number, self.to_number]):
            self.client = Client(self.account_sid, self.auth_token)
            logger.info(f"Call service initialized successfully. From: {self.from_number}, To: {self.to_number}")
        else:
            missing = []
            if not self.account_sid: missing.append("TWILIO_ACCOUNT_SID")
            if not self.auth_token: missing.append("TWILIO_AUTH_TOKEN")
            if not self.from_number: missing.append("TWILIO_PHONE_NUMBER")
            if not self.to_number: missing.append("ALERT_PHONE_NUMBER")
            logger.warning(f"Call service not fully configured. Missing: {', '.join(missing)}")

    def _analyze_threat_with_ai(self, threat_level, location, summary, analysis_data):
        """Use OpenAI to analyze the threat and provide guidance"""
        try:
            # Extract relevant information from analysis_data
            profiles = analysis_data.get('profiles', []) if analysis_data else []
            weapons = analysis_data.get('weapons', []) if analysis_data else []
            recommended_response = analysis_data.get('recommended_response', 'No specific action needed.') if analysis_data else 'No specific action needed.'
            
            # Prepare the context for the AI
            context = f"""
            You are a security expert analyzing a live security feed. Provide a detailed analysis and immediate action plan.

            Current Situation:
            - Threat Level: {threat_level}
            - Location: {location}
            - Summary: {summary}
            - Detected Profiles: {', '.join(profiles) if profiles else 'None'}
            - Potential Weapons: {', '.join(weapons) if weapons else 'None'}
            - System Recommendation: {recommended_response}

            Please provide a detailed response in the following format:
            1. SITUATION ASSESSMENT:
               - What is happening in the video
               - Level of immediate danger
               - Number of people involved
               - Any visible weapons or threatening objects

            2. IMMEDIATE ACTIONS REQUIRED:
               - Step-by-step actions to take right now
               - Whether to contact emergency services (police at 100, fire, etc.)
               - Specific emergency numbers to call
               - Safety measures to implement immediately

            3. PRECAUTIONARY MEASURES:
               - Additional security steps to take
               - Areas to secure or evacuate
               - Communication protocols to follow

            Make the response clear, concise, and immediately actionable. Focus on protecting life and property.
            """
            
            # Get AI response
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a security expert assistant providing real-time threat analysis and immediate action guidance. Be specific, clear, and focus on immediate actions needed to protect life and property."},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Failed to analyze threat with AI: {str(e)}")
            return "Unable to analyze threat with AI. Please take standard security precautions and contact emergency services if needed."

    def make_alert_call(self, threat_level, location, summary=None, analysis_data=None):
        """
        Make a phone call when a threat is detected
        
        Args:
            threat_level (str): The level of threat (LOW, MEDIUM, HIGH, CRITICAL)
            location (str): The location where the threat was detected
            summary (str, optional): Additional information about the threat
            analysis_data (dict, optional): Detailed analysis data from the detection system
        """
        if not self.client:
            logger.error("Call service not properly configured")
            return False

        try:
            # Get AI analysis and guidance
            ai_guidance = self._analyze_threat_with_ai(threat_level, location, summary, analysis_data)
            
            # Create a message for the call
            message = f"Security Alert! {threat_level} level threat detected at {location}. "
            if summary:
                message += f"Initial assessment: {summary}. "
            message += f"Security Expert Analysis and Guidance: {ai_guidance}"

            # Format the message for Twilio's voice system
            twiml = f"""
            <Response>
                <Say voice="Polly.Amy" language="en-GB">
                    {message}
                </Say>
            </Response>
            """

            # Make the call using Twilio
            call = self.client.calls.create(
                to=self.to_number,
                from_=self.from_number,
                twiml=twiml
            )
            
            logger.info(f"Alert call initiated with detailed AI guidance. Call SID: {call.sid}")
            logger.info(f"Calling from {self.from_number} to {self.to_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to make alert call: {str(e)}")
            return False 