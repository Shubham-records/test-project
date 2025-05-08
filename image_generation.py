import base64
import os
import random
import string
from typing import Optional, Dict, Any, List, Union
from together import Together
import api_keys

class ImageGeneration:
    def __init__(self):
        self.api_key = api_keys.BLACK_FOREST_LABS_API_KEY
        self.model = api_keys.BLACK_FOREST_LABS_MODEL
        self.client = Together(api_key=self.api_key)
    
    def generate_image(self, 
                      prompt: str,
                      width: int = 1280,
                      height: int = 720,
                      steps: int = 4,
                      n: int = 1,
                      save_path: Optional[str] = None) -> Dict[str, Any]:
        
        response = self.client.images.generate(
            prompt=prompt,
            model=self.model,
            width=width,
            height=height,
            steps=steps,
            n=n,
            response_format="b64_json"
        )
        
        # Get the base64 encoded image data
        image_data = response.data[0].b64_json
        
        result = {
            "response": response,
            "image_data": image_data
        }
        
        # Save the image if a path is provided
        if save_path:
            self.save_image(image_data, save_path)
            result["saved_path"] = save_path
        
        return result
    
    def save_image(self, image_data: str, output_path: Optional[str] = None) -> str:
        if not image_data:
            raise ValueError("No image data provided")
        
        # Generate a random filename if none provided
        if not output_path:
            random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            output_path = f"{random_name}.png"
        
        try:
            # Decode the base64 data and write to file
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(image_data))
            
            print(f"Image saved to {output_path}")
            print(f"File size: {os.path.getsize(output_path)} bytes")
            return output_path
        except Exception as e:
            print(f"Error saving image: {str(e)}")
            
            # Debug information
            print("\nDebug Info:")
            print(f"Data type: {type(image_data)}")
            print(f"Data length: {len(image_data) if hasattr(image_data, '__len__') else 'unknown'}")
            raise

if __name__ == "__main__":
    pass