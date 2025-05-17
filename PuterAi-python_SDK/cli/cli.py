import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

url = 'https://api.puter.com/drivers/call'
headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Authorization': f"Bearer {os.getenv('API_TOKEN')}",
    'Connection': 'keep-alive',
    'Content-Type': 'application/json;charset=UTF-8',
    'Origin': 'https://docs.puter.com',
    'Referer': 'https://docs.puter.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
}

conversation_history = []

def mowhn(message):
    conversation_history.append({"content": message})
    data = {
        "interface": "puter-chat-completion",
        "driver": "openai-completion",
        "test_mode": False,
        "method": "complete",
        "args": {
            "messages": conversation_history
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        response_json = response.json()
        if response_json.get("success"):
            bot_reply = response_json['result']['message']['content']
            conversation_history.append({"content": bot_reply, "role": "assistant"})
            return bot_reply
        else:
            return "Failed to get a valid response from the API."
    else:
        return f"Request failed with status code {response.status_code}"

def puter(user_text):
    data = {
        "interface": "puter-tts",
        "driver": "aws-polly",
        "test_mode": False,
        "method": "synthesize",
        "args": {
            "text": user_text
        }
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        with open('output_file.mp3', 'wb') as file:
            file.write(response.content)
        print("MP3 file has been saved as 'output_file.mp3'.")
    else:
        print(f"Failed to retrieve the file. Status code: {response.status_code}")

def mowhn_chat():
    print("Chatbot: Hello! How can I assist you today?")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Chatbot: Goodbye!")
            break
        bot_response = mowhn(user_input)
        print(f"Chatbot: {bot_response}")

def main():
    print("Welcome! Please choose an option:")
    print("1. Chat")
    print("2. Generate Text to Speech (TTS)")
    choice = input("Enter the number of your choice: ")
    if choice == "1":
        mowhn_chat()
    elif choice == "2":
        user_text = input("Enter the text you want to synthesize: ")
        puter(user_text)
    else:
        print("Invalid choice. Please select either 1 or 2.")

main()