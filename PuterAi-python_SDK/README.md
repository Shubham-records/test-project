
# PuterAi-python_SDK

PuterAi Python SDK provides a simple way to interact with the Puter AI API for chatbot interactions and text-to-speech (TTS) generation. This SDK allows you to integrate chatbot and TTS functionalities into your own applications.

## Features

- **Chatbot Interaction**: Communicate with a chatbot powered by Puter AI.
- **Text-to-Speech (TTS)**: Convert any text into audio using AWS Polly TTS service.

## Project Structure

The project consists of multiple components:

- **`login.py`**: Script to handle user login and retrieve an API token for further requests.
- **`cli.py`**: Command-line interface that allows users to interact with the Puter chatbot or generate TTS output.
- **`server.py`**: A Flask-based API server that exposes endpoints for chatbot and TTS functionalities.
- **`example.html`**: A simple HTML front-end to interact with the chatbot and generate TTS via a browser.

## Requirements

To run this project, you need to install the following dependencies:

- `requests`: To handle HTTP requests.
- `flask`: For the API server.
- `flask_cors`: For handling Cross-Origin Resource Sharing (CORS).
- `dotenv`: To load environment variables from a .env file.

You can install the required dependencies with:

```bash
pip install -r requirements.txt
```

## Setup Instructions

1. **Clone the Repository**

```bash
git clone https://github.com/mowhn/PuterAi-python_SDK.git
cd puterAi-python_SDK
```

2. **Setup .env File in Both CLI and API Folders**

Create a `.env` file in both the `cli` and `API` directories and include your API_TOKEN:

```env
API_TOKEN=your_api_token_here
```

3. **Get the API Token**

To quickly obtain your `API_TOKEN`, you must first run `login.py` to log in and retrieve the token:

- Run `login.py`:

  ```bash
  cd cli
  python login.py
  ```

  This will prompt you for your username and password, and if the login is successful, it will output the `API_TOKEN`. You can copy this token and paste it into the `.env` file in both the `cli` and `API` folders.

  **Note**: If you don't have a Puter AI account, you can sign up at <a href="https://puter.com/?r=J1YOKLC5" target="_blank">
  <img src="https://img.shields.io/badge/Sign%20Up%20for%20PuterAI-Click%20Here-brightgreen" alt="Sign Up for PuterAI" />
</a>

4. **Running the Project**

- Run the API Server:

  ```bash
  cd API
  python server.py
  ```

  This will start the Flask API server on `http://localhost:5000`.

- Use the Command-Line Interface (CLI):

  To interact with the chatbot or generate TTS from the command line, run:

  ```bash
  cd cli
  python cli.py
  ```

5. **Front-End Example**

Open the `example.html` file in a browser to interact with the Puter chatbot and generate TTS:

- **Chat with the Bot**: Enter a message and receive a response from the bot.
- **Generate TTS**: Enter text to convert into speech, and play the generated audio.

## Endpoints

The Flask API exposes the following endpoints:

- **POST `/chat`**: Accepts a JSON object with a `message` field and returns a bot response.

  Example request:

  ```json
  {
    "message": "Hello, bot!"
  }
  ```

- **POST `/tts`**: Accepts a JSON object with a `text` field and returns the corresponding TTS audio.

  Example request:

  ```json
  {
    "text": "Hello, this is a test."
  }
  ```


## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/mowhn/PuterAi-python_SDK/blob/main/LICENSE) file for details.

---

Enjoy building with Puter!
