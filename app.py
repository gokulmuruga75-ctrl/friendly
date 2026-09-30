import os
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from google import genai
from google.genai import types
from chatbot_config import SYSTEM_PROMPT

load_dotenv()
app = Flask(__name__)
MODEL_NAME = os.getenv('GEMINI_MODEL', 'gemini-3.1-flash-lite')
API_KEY = os.getenv('GEMINI_API_KEY')
if not API_KEY:
    raise RuntimeError('GEMINI_API_KEY is missing from the .env file.')
client = genai.Client(api_key=API_KEY)

@app.get('/')
def home():
    return render_template('index.html')

@app.post('/chat')
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()
    history = data.get('history') or []
    if not message:
        return jsonify({'error': 'Please enter a question.'}), 400

    contents = []
    for item in history[-12:]:
        if isinstance(item, dict) and item.get('role') in {'user', 'model'} and isinstance(item.get('content'), str):
            text = item['content'].strip()
            if text:
                contents.append(types.Content(role=item['role'], parts=[types.Part.from_text(text=text)]))
    contents.append(types.Content(role='user', parts=[types.Part.from_text(text=message)]))

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                thinking_config=types.ThinkingConfig(thinking_level='low'),
            ),
        )
        answer = (response.text or '').strip() or 'I could not generate a response right now.'
        return jsonify({'response': answer})
    except Exception:
        app.logger.exception('Gemini API request failed')
        return jsonify({'error': 'I could not connect to Friendly right now. Please try again.'}), 500

if __name__ == '__main__':
    app.run(host=os.getenv('FLASK_HOST', '127.0.0.1'), port=int(os.getenv('FLASK_PORT', '5000')), debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true')
