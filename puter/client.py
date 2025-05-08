import requests
import json
from typing import List, Dict, Any, Union
from rich.console import Console

console = Console(highlight=False)

class PuterAI:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("api key is required")
        self.url = "https://api.puter.com/drivers/call"
        self.api_key = api_key
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Authorization": f"Bearer {api_key}",
            "Connection": "keep-alive",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://playground.puter.site",
            "Referer": "https://playground.puter.site/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Chromium";v="135", "Not-A.Brand";v="8"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        }

    def create_completion(self, 
                         messages: List[Dict[str, str]], 
                         model: str = "gpt-4o-mini",
                         driver: str = "openai-completion",
                         stream: bool = False) -> Union[Dict[str, Any], str]:
        """create a chat completion"""
        # Format messages properly if they don't have role
        formatted_messages = []
        for msg in messages:
            if "role" not in msg and "content" in msg:
                formatted_messages.append({"role": "user", "content": msg["content"]})
            else:
                formatted_messages.append(msg)
                
        payload = {
            "interface": "puter-chat-completion",
            "driver": driver,
            "test_mode": False,
            "method": "complete",
            "args": {
                "messages": formatted_messages,
                "model": model
            }
        }
        
        # Add stream parameter only if it's True
        if stream:
            payload["args"]["stream"] = stream
            
        return self._send_request(payload, expect_json=True)
    
    def create_image(self, 
                    prompt: str,
                    model: str = None) -> Dict[str, Any]:
        """create an image from a text prompt"""
        payload = {
            "interface": "puter-image-generation",
            "test_mode": False,
            "method": "generate",
            "args": {
                "prompt": prompt
            }
        }
        
        # Add model if specified
        if model:
            payload["args"]["model"] = model
            
        # Image generation returns binary data directly, not JSON
        return self._send_request(payload, expect_json=False)

    def _send_request(self, payload: Dict[str, Any], expect_json: bool = True) -> Dict[str, Any]:
        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                if expect_json:
                    return response.json()
                else:
                    # For image generation, return the raw binary content
                    return {
                        "success": True,
                        "image_data": response.content,  # Use .content instead of .text for binary data
                        "content_type": response.headers.get("Content-Type", "")
                    }
            
            error_msg = {
                401: "invalid api key",
                403: "forbidden - check your api key",
                429: "too many requests",
                500: "server error"
            }.get(response.status_code, f"request failed: {response.text}")
            return {"error": error_msg, "status": response.status_code}
            
        except requests.RequestException as e:
            return {"error": f"network error: {str(e)}", "status": 0}
        except Exception as e:
            return {"error": f"unexpected error: {str(e)}", "status": -1}