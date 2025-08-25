import requests
import json
from typing import Dict, Any, List
from config import settings
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    def generate(self, prompt: str, context: List[str] = None, temperature: float = 0.1) -> str:
        """Generate a response using the Ollama API"""
        try:
            # Build the full prompt with context
            full_prompt = self._build_prompt(prompt, context)
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "temperature": temperature,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120  # Longer timeout for generation
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return "Sorry, I couldn't process your request at this time."
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Ollama failed: {e}")
            return "Connection to the AI service failed. Please try again later."
    
    def _build_prompt(self, prompt: str, context: List[str] = None) -> str:
        """Build a prompt with context for the model"""
        if not context:
            return prompt
            
        context_str = "\n".join([f"Context {i+1}: {ctx}" for i, ctx in enumerate(context)])
        return f"""Based on the following context:

{context_str}

Please respond to this query: {prompt}

Your response should be helpful, concise, and focused on solving the problem."""
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama"""
        try:
            payload = {
                "model": self.model,
                "prompts": texts
            }
            
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return [embedding.get("embedding", []) for embedding in result.get("embeddings", [])]
            else:
                logger.error(f"Ollama embeddings error: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Ollama embeddings failed: {e}")
            return []

ollama_client = OllamaClient()