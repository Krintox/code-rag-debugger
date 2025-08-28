import requests
import json
from typing import Dict, Any, List
from config import settings
import logging

logger = logging.getLogger(__name__)

class DeepInfraClient:
    def __init__(self):
        self.api_key = settings.DEEPINFRA_API_KEY
        self.model = settings.DEEPINFRA_MODEL
        self.base_url = "https://api.deepinfra.com/v1/inference"

    def generate(self, prompt: str, context: List[str] = None, temperature: float = 0.1) -> str:
        """Generate a response using the DeepInfra API"""
        try:
            # Build the full prompt with context
            full_prompt = self._build_prompt(prompt, context)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "input": full_prompt,
                "temperature": temperature,
                "max_new_tokens": 1024,
                "stop": ["</s>", "###"]
            }
            
            response = requests.post(
                f"{self.base_url}/{self.model}",
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("results", [{}])[0].get("generated_text", "").strip()
            else:
                logger.error(f"DeepInfra API error: {response.status_code} - {response.text}")
                return "Sorry, I couldn't process your request at this time."
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to DeepInfra failed: {e}")
            return "Connection to the AI service failed. Please try again later."
    
    def _build_prompt(self, prompt: str, context: List[str] = None) -> str:
        """Build a prompt with context for the model"""
        if not context:
            return prompt
            
        context_str = "\n".join([f"Context {i+1}: {ctx}" for i, ctx in enumerate(context)])
        return f"""Based on the following context:

{context_str}

Please respond to this query: {prompt}

Your response should be helpful, concise, and focused on solving the problem.

Response:"""
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using DeepInfra"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": texts,
                "truncate": True
            }
            
            response = requests.post(
                f"{self.base_url}/sentence-transformers/all-MiniLM-L6-v2",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                logger.error(f"DeepInfra embeddings error: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to DeepInfra embeddings failed: {e}")
            return []

deepinfra_client = DeepInfraClient()