from pathlib import Path
import os
import random
import string
import api_keys

class ChatCompletion:
    @staticmethod
    def create(messages, model="gpt-4o", driver="openai-completion", api_key=None):
        from puter import ChatCompletion as PuterChatCompletion
        
        if api_key is None:
            # Use API key from api_keys.py
            api_key = api_keys.PUTER_API_KEY
            
        response = PuterChatCompletion.create(
            messages=messages,
            model=model,
            driver=driver,
            api_key=api_key
        )
        
        return response


class ImageGeneration:
    @staticmethod
    def create(prompt, api_key=None, save_to_file=False):
        from puter import ImageGeneration as PuterImageGeneration
        
        if api_key is None:
            # Use API key from api_keys.py
            api_key = api_keys.PUTER_API_KEY
            
        response = PuterImageGeneration.create(
            prompt=prompt,
            api_key=api_key
        )
        
        result = {"response": response}
        
        if "error" in response:
            result["error"] = response["error"]
            return result
            
        # Get the image data
        image_data = response["image_data"]
        result["image_data"] = image_data
        
        # Save to file if requested
        if save_to_file:
            # Generate a random filename (10 characters)
            random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            output_path = f"{random_name}.png"
            
            try:
                # Write binary data directly to file
                with open(output_path, "wb") as f:
                    f.write(image_data)
                
                print(f"Image saved to {output_path}")
                print(f"File size: {os.path.getsize(output_path)} bytes")
                result["file_path"] = output_path
            except Exception as e:
                print(f"Error saving image: {str(e)}")
                result["error"] = str(e)
                
                # Debug information
                print("\nDebug Info:")
                print(f"Data type: {type(image_data)}")
                print(f"Data length: {len(image_data) if hasattr(image_data, '__len__') else 'unknown'}")
        
        return result


# Example usage
def example_usage():
    # Example 1: Chat Completion
    chat_response = ChatCompletion.create(
        messages=[{"role": "user", "content": "What is the capital of France?"}],
        model="gpt-4o",
        driver="openai-completion"
    )
    
    print("Chat Completion Response:")
    print(chat_response)

    chat_response = ChatCompletion.create(
        messages=[{"role": "user", "content": "What is the capital of France?"}],
        model="claude-3-5-sonnet-latest",
        driver="claude"
    )
    
    print("Chat Completion Response:")
    print(chat_response['result']['message']['content'][0]['text'])
    
    # Example 2: Image Generation
    image_response = ImageGeneration.create(
        prompt="A beautiful sunset over Paris",
        save_to_file=True
    )
    
    if "error" in image_response:
        print(f"Error: {image_response['error']}")
    else:
        print("Image generated successfully!")
        if "file_path" in image_response:
            print(f"Saved to: {image_response['file_path']}")


if __name__ == "__main__":
    # Uncomment to run the example
    # example_usage()
    pass