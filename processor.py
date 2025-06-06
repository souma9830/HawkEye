import os
import time
import base64
import json
import re
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

def process_screenshot(image_path):
    """
    Analyzes the given image using the specified OpenAI-compatible model to detect humans,
    potential weapons, danger level, and whether action is required.
    Always returns a consistent structure with multiple threat levels.
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[PROCESSING] {image_path}")

    try:
        image_base64 = _to_base64(image_path)

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a security assistant analyzing images. "
                        "Do not identify or make assumptions about specific individuals. "
                        "Instead, describe visible people's posture (e.g., sitting, running), visible object types "
                        "(e.g., bags, tools, weapons), and potential threats. Return the following fields:\n"
                        "- summary: brief description of what's happening in the image\n"
                        "- profiles: list of descriptions of each human\n"
                        "- weapons: list of any objects resembling weapons\n"
                        "- danger: categorize as 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'\n"
                        "- action_required: true/false flag\n"
                        "- recommended_response: specific action recommendation based on threat level\n"
                        "Respond strictly in JSON format only. Avoid vague statements or refusals."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this image and return the structured information as instructed."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ],
            temperature=0.2,
            max_tokens=1000
        )

        raw_text = response.choices[0].message.content
        structured = _safe_parse_json(raw_text)

        if "sorry" in raw_text.lower() or not structured:
            raise ValueError("Model refused or failed to respond with structured data.")

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
        print(f"[ERROR] during image analysis: {e}")
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

def _to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def _safe_parse_json(text):
    try:
        if text.startswith("```json"):
            text = re.sub(r"```json|```", "", text).strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {}