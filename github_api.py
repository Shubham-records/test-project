import api_keys
from openai import OpenAI

class GitHubCompletion:
    @staticmethod
    def create(messages, model="openai/gpt-4o", temperature=1, max_tokens=4096, top_p=1):
        # Get all available API keys
        api_keys_list = api_keys.GITHUB_TOKEN if isinstance(api_keys.GITHUB_TOKEN, list) else [api_keys.GITHUB_TOKEN]
        
        # Try with all available API keys
        last_error = None
        for current_api_key in api_keys_list:
            try:
                # Create client with current API key
                client = OpenAI(base_url="https://models.github.ai/inference", api_key=current_api_key)
                
                # Make the API call
                response = client.chat.completions.create(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p
                )
                
                # Return the response content
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                print(f"Error with GitHub API using token {current_api_key[:10]}...: {str(e)}")
                continue
        
        # If we get here, all attempts failed
        error_msg = f"All GitHub API attempts failed. Last error: {str(last_error)}"
        print(error_msg)
        return {"error": error_msg}


if __name__ == "__main__":
    response = GitHubCompletion.create([
        {"role": "system", "content": ""},
        {"role": "user", "content": "What is the capital of France?"}
    ])
    
    if isinstance(response, dict) and "error" in response:
        print(f"Error: {response['error']}")
    else:
        print(response)
