import requests
import logging
from typing import List, Optional
from config import settings

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    def generate(self, prompt: str, context: Optional[List[str]] = None) -> str:
        """Generate a response using Gemini API (Google Generative Language API)"""
        if not self.api_key:
            logger.error("Gemini API key is missing")
            return "API service is currently unavailable"

        try:
            full_prompt = self._build_prompt(prompt, context)

            headers = {
                "Content-Type": "application/json"
            }

            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": full_prompt
                            }
                        ]
                    }
                ]
            }

            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                data = response.json()
                # Gemini's expected response format
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
                except (KeyError, IndexError) as e:
                    logger.error(f"Unexpected Gemini API response format: {data}")
                    return "Unexpected response format from API"
            else:
                logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                return "Sorry, I couldn't process your request at this time."

        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Gemini API failed: {e}")
            return "Connection to the AI service failed. Please try again later."

    def _build_prompt(self, prompt: str, context: Optional[List[str]] = None) -> str:
        """Build a prompt with optional context"""
        if not context:
            return prompt

        context_str = "\n".join([f"Context {i+1}: {ctx}" for i, ctx in enumerate(context)])
        return f"""Based on the following context:

{context_str}

Please respond to this query: {prompt}

Your response should be helpful, concise, and focused on solving the problem.

Response:"""


gemini_client = GeminiClient()
