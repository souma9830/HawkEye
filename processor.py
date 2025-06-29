import os
import time
import base64
import json
import re
import traceback
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv
from PIL import Image
import io

# Load environment variables
load_dotenv(find_dotenv())

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("[ERROR] GEMINI_API_KEY not found in environment variables")
    print("[INFO] Please set GEMINI_API_KEY in your .env file")
    print("[INFO] You can get an API key from: https://makersuite.google.com/app/apikey")
    raise ValueError("GEMINI_API_KEY not found in environment variables")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    print("[INFO] Successfully configured Gemini API")
except Exception as e:
    print(f"[ERROR] Failed to configure Gemini API: {e}")
    raise

def process_screenshot(image_path):
    """
    Analyzes the given image using Google's Gemini model to detect humans,
    potential weapons, danger level, and whether action is required.
    Always returns a consistent structure with multiple threat levels.
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[PROCESSING] {image_path}")

    try:
        # Initialize Gemini Pro Vision model
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            print("[INFO] Successfully initialized Gemini model")
        except Exception as e:
            print(f"[ERROR] Failed to initialize Gemini model: {e}")
            raise
        
        # Load and prepare the image
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
                
            with Image.open(image_path) as img:
                print(f"[DEBUG] Original image size: {img.size}, mode: {img.mode}")
                
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    print("[DEBUG] Converted image to RGB")
                
                # Resize if too large (Gemini has size limits)
                max_size = (1024, 1024)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    print(f"[DEBUG] Resized image to: {img.size}")
                
                # Save to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=95)
                image_data = img_byte_arr.getvalue()
                print(f"[DEBUG] Image data size: {len(image_data)} bytes")
                
                # Convert bytes to PIL Image for Gemini API
                image_for_api = Image.open(io.BytesIO(image_data))
                
        except Exception as e:
            print(f"[ERROR] Image processing failed: {str(e)}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            raise ValueError(f"Failed to process image: {str(e)}")
        
        # Create the prompt
        prompt = """
        Analyze this security camera image and provide a structured assessment. Focus on:
        1. Visible people and their postures/actions
        2. Any objects that could be weapons
        3. Overall threat level
        4. Whether immediate action is required
        
        Return the response in this exact JSON format:
        {
            "summary": "brief description of the scene",
            "profiles": ["list of human descriptions"],
            "weapons": ["list of potential weapons"],
            "danger": "LOW/MEDIUM/HIGH/CRITICAL",
            "action_required": true/false,
            "recommended_response": "specific action recommendation"
        }
        """
        
        print("[DEBUG] Sending request to Gemini API...")
        
        # Generate content with safety settings
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
        
        try:
            response = model.generate_content(
                [prompt, image_for_api],
                safety_settings=safety_settings,
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            print("[DEBUG] Received response from Gemini API")
        except Exception as e:
            print(f"[ERROR] Gemini API request failed: {e}")
            raise
        
        if not response:
            raise ValueError("Empty response from model")
            
        if not response.text:
            raise ValueError("No text in model response")
            
        raw_text = response.text
        print(f"[DEBUG] Raw response: {raw_text[:200]}...")  # Print first 200 chars
        
        # Extract JSON from response
        structured = _safe_parse_json(raw_text)
        
        if not structured:
            print("[DEBUG] Failed to parse JSON from response")
            print(f"[DEBUG] Raw text that failed to parse: {raw_text}")
            raise ValueError("Failed to parse structured data from model response")
        
        if "sorry" in raw_text.lower():
            raise ValueError("Model refused to analyze the image")

        return {
            "status": "success",
            "timestamp": timestamp,
            "image_path": image_path,
            "summary": structured.get("summary", "No summary available."),
            "profiles": structured.get("profiles", []),
            "weapons": structured.get("weapons", []),
            "danger": structured.get("danger", "LOW"),
            "action_required": structured.get("action_required", False),
            "recommended_response": structured.get("recommended_response", "No specific action needed."),
            "raw_model_response": raw_text
        }

    except Exception as e:
        print(f"[ERROR] during image analysis: {str(e)}")
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "timestamp": timestamp,
            "image_path": image_path,
            "error": str(e),
            "summary": "Unable to analyze due to error.",
            "profiles": [],
            "weapons": [],
            "danger": "Unable to analyze due to error.",
            "action_required": False,
            "recommended_response": "System error - review manually.",
            "raw_model_response": None
        }

def _safe_parse_json(text):
    """Safely parse JSON from text, handling common issues"""
    try:
        # First try direct JSON parsing
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            # Try to extract JSON from text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
    return None