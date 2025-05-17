from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import requests
from io import BytesIO
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

url = 'https://api.puter.com/drivers/call'
headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Authorization': f"Bearer {os.getenv('API_TOKEN')}",
    'Connection': 'keep-alive',
    'Content-Type': 'application/json;charset=UTF-8',
    'Origin': 'https://docs.puter.com',
    'Referer': 'https://docs.puter.com/',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
}

conversation_history = []

def mowhn(message):
    conversation_history.append({"content": message})
    data = {
        "interface": "puter-chat-completion",
        "driver": "openai-completion",
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
        return "Failed to get a valid response from the API."
    return f"Request failed with status code {response.status_code}"

def puter(user_text):
    data = {
        "interface": "puter-tts",
        "driver": "aws-polly",
        "method": "synthesize",
        "args": {
            "text": user_text
        }
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        return BytesIO(response.content)
    return None

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    if user_input:
        bot_response = mowhn(user_input)
        return jsonify({'response': bot_response})
    return jsonify({'error': 'No message provided'}), 400

@app.route('/tts', methods=['POST'])
def tts():
    user_text = request.json.get('text')
    if user_text:
        audio_data = puter(user_text)
        if audio_data:
            return send_file(audio_data, mimetype='audio/mp3', as_attachment=False)
        return jsonify({'error': 'Failed to generate TTS'}), 500
    return jsonify({'error': 'No text provided'}), 400

if __name__ == '__main__':
    app.run(debug=True)