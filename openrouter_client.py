import requests
import json
import os
from typing import List, Dict, Any, Optional

class OpenRouterClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/alexolinux/openrouter-cli", # Optional, for OpenRouter rankings
            "X-Title": "OpenRouter CLI",                                    # Optional
            "Content-Type": "application/json"
        }

    def get_free_models(self) -> List[Dict[str, Any]]:
        """
        Fetches all models and filters for those with zero pricing.
        """
        try:
            url = f"{self.base_url}/models"
            response = requests.get(url)
            response.raise_for_status()
            
            models = response.json().get('data', [])
            free_models = []
            
            for model in models:
                pricing = model.get('pricing', {})
                # Check if both prompt and completion are "0" (as strings or numbers)
                is_free = (
                    str(pricing.get('prompt')) == "0" and 
                    str(pricing.get('completion')) == "0"
                )
                if is_free:
                    free_models.append(model)
            
            return sorted(free_models, key=lambda x: x.get('name', ''))
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []

    def chat_completion(self, model_id: str, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        Sends a chat completion request to OpenRouter.
        """
        try:
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": model_id,
                "messages": messages
            }
            
            response = requests.post(url, headers=self.headers, data=json.dumps(payload))
            response.raise_for_status()
            
            result = response.json()
            choices = result.get('choices', [])
            if choices:
                return choices[0].get('message', {}).get('content')
            return None
        except Exception as e:
            print(f"\nError during chat completion: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"Details: {json.dumps(error_detail, indent=2)}")
                except:
                    pass
            return None
