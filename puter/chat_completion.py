from typing import List, Dict, Any, Union
from .client import PuterAI

class ChatCompletion:
    @staticmethod
    def create(messages: List[Dict[str, str]], 
               model: str = "gpt-4o-mini",  
               driver: str = "openai-completion",
               stream: bool = False,
               api_key: str = None) -> Union[Dict[str, Any], str]:
        """openai-style chat completion"""
        client = PuterAI(api_key=api_key)
        return client.create_completion(messages, model=model, driver=driver, stream=stream)

class ImageGeneration:
    @staticmethod
    def create(prompt: str,
               model: str = None,
               api_key: str = None) -> Dict[str, Any]:
        """generate an image from a text prompt"""
        client = PuterAI(api_key=api_key)
        return client.create_image(prompt, model=model)