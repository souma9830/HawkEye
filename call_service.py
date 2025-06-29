from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import os
from datetime import datetime
import logging
import google.generativeai as genai
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
        
        # Initialize Gemini
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Enhanced debugging
        logger.info("=== Call Service Configuration ===")
        logger.info(f"TWILIO_ACCOUNT_SID: {'✓ Set' if self.account_sid else '✗ Missing'}")
        logger.info(f"TWILIO_AUTH_TOKEN: {'✓ Set' if self.auth_token else '✗ Missing'}")
        logger.info(f"TWILIO_PHONE_NUMBER: {'✓ Set' if self.from_number else '✗ Missing'}")
        logger.info(f"ALERT_PHONE_NUMBER: {'✓ Set' if self.to_number else '✗ Missing'}")
        logger.info(f"GOOGLE_API_KEY: {'✓ Set' if os.getenv('GOOGLE_API_KEY') else '✗ Missing'}")
        
        if all([self.account_sid, self.auth_token, self.from_number, self.to_number]):
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info(f"✓ Call service initialized successfully")
                logger.info(f"  From: {self.from_number}")
                logger.info(f"  To: {self.to_number}")
            except Exception as e:
                logger.error(f"✗ Failed to initialize Twilio client: {e}")
                self.client = None
        else:
            missing = []
            if not self.account_sid: missing.append("TWILIO_ACCOUNT_SID")
            if not self.auth_token: missing.append("TWILIO_AUTH_TOKEN")
            if not self.from_number: missing.append("TWILIO_PHONE_NUMBER")
            if not self.to_number: missing.append("ALERT_PHONE_NUMBER")
            logger.warning(f"✗ Call service not fully configured. Missing: {', '.join(missing)}")
            logger.warning("To enable phone call alerts, create a .env file with the missing variables")

    def _analyze_threat_with_ai(self, threat_level, location, summary, analysis_data):
        """Use Gemini to analyze the threat and provide guidance"""
        try:
            # Extract relevant information from analysis_data
            profiles = analysis_data.get('profiles', []) if analysis_data else []
            weapons = analysis_data.get('weapons', []) if analysis_data else []
            recommended_response = analysis_data.get('recommended_response', 'No specific action needed.') if analysis_data else 'No specific action needed.'
            
            # Prepare the context for the AI with a request for brevity
            context = f"""
            You are a security expert analyzing a live security feed. Provide a BRIEF analysis and immediate action plan.
            Keep your response under 200 words and focus on the most critical information.

            Current Situation:
            - Threat Level: {threat_level}
            - Location: {location}
            - Summary: {summary}
            - Detected Profiles: {', '.join(profiles) if profiles else 'None'}
            - Potential Weapons: {', '.join(weapons) if weapons else 'None'}
            - System Recommendation: {recommended_response}

            Provide a concise response with:
            1. Immediate threat assessment
            2. Critical actions needed
            3. Key safety measures

            Keep it brief and actionable.
            """
            
            # Get AI response using Gemini
            response = self.model.generate_content(context)
            
            # Truncate response if needed and ensure it's properly formatted
            ai_response = response.text.strip()
            if len(ai_response) > 500:  # Set a reasonable limit
                ai_response = ai_response[:497] + "..."
            
            return ai_response
            
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
        logger.info(f"=== Making Alert Call ===")
        logger.info(f"Threat Level: {threat_level}")
        logger.info(f"Location: {location}")
        logger.info(f"Summary: {summary}")
        
        if not self.client:
            logger.error("✗ Call service not properly configured - cannot make call")
            return False

        try:
            # Get AI analysis and guidance
            ai_guidance = self._analyze_threat_with_ai(threat_level, location, summary, analysis_data)
            logger.info(f"AI Guidance generated: {len(ai_guidance)} characters")
            
            # Create a concise message for the call
            message = f"Security Alert! {threat_level} level threat at {location}. "
            if summary:
                # Truncate summary if too long
                summary = summary[:100] + "..." if len(summary) > 100 else summary
                message += f"Initial assessment: {summary}. "
            
            # Add AI guidance with size check
            message += f"Security Analysis: {ai_guidance}"

            # Create TwiML response using Twilio's builder
            response = VoiceResponse()
            
            # Split message into smaller chunks if needed
            max_chunk_size = 1000  # Twilio's recommended chunk size
            message_chunks = [message[i:i+max_chunk_size] for i in range(0, len(message), max_chunk_size)]
            
            # Add each chunk as a separate Say verb
            for chunk in message_chunks:
                response.say(chunk, voice='Polly.Amy', language='en-GB')
                response.pause(length=1)  # Add a small pause between chunks
            
            # Add closing message
            response.say("This is an automated security alert. Please take necessary actions.", 
                        voice='Polly.Amy', 
                        language='en-GB')

            # Convert TwiML to string
            twiml = str(response)

            # Make the call using Twilio
            logger.info(f"Making call from {self.from_number} to {self.to_number}")
            call = self.client.calls.create(
                to=self.to_number,
                from_=self.from_number,
                twiml=twiml
            )
            
            logger.info(f"✓ Alert call initiated successfully!")
            logger.info(f"  Call SID: {call.sid}")
            logger.info(f"  Status: {call.status}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to make alert call: {str(e)}")
            logger.error(f"  Error type: {type(e).__name__}")
            return False 