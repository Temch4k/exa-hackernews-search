from flask import Flask, request, jsonify
from flask_cors import CORS 
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
from waitress import serve
import logging

load_dotenv()

# Set up logging based on DEBUG_MODE env var
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

EXA_API_URL = os.getenv("EXA_API_URL")
EXA_API_KEY = os.getenv("EXA_API_KEY")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = Flask(__name__)
CORS(app)  

@app.route('/')
def index():
    return jsonify({"Choo Choo": "Welcome to your Flask app 🚅"})

@app.route("/query_exa_search", methods=['POST'])
def query_exa_search():
    data = request.get_json()
    user_input = data.get('user_input')
    
    headers = {"x-api-key": EXA_API_KEY, "Content-Type": "application/json"}
    payload = {
        "query": user_input, 
        "numResults": 6, 
        "includeDomains": ["news.ycombinator.com/"]
    }

    try:
        response = requests.post(EXA_API_URL+"/search", headers=headers, json=payload)
        response.raise_for_status()
        logger.debug(f"Search API response status: {response.status_code}")
        return jsonify({"results": response.json()})
    except requests.exceptions.RequestException as e:
        logger.error(f"Error details: {str(e)}")
        return jsonify({
            "error": f"Error communicating with EXA API: {str(e)}"
        }), 500

@app.route("/query_exa_content", methods=['POST'])
def query_exa_content():
    data = request.get_json()
    user_input = data.get('user_input')
    
    headers = {"x-api-key": EXA_API_KEY, "Content-Type": "application/json"}
    payload = {"ids": [user_input]}

    try:
        response = requests.post(EXA_API_URL+"/contents", headers=headers, json=payload)
        logger.debug(f"Content API response status: {response.status_code}")
        response.raise_for_status()
        return jsonify({"content": response.json()})
    except requests.exceptions.RequestException as e:
        logger.error(f"Error details: {str(e)}")
        return jsonify({
            "error": f"Error communicating with EXA Content API: {str(e)}"
        }), 500

@app.route("/query_exa_chat", methods=['POST'])
def chat_exa():
    data = request.get_json()
    user_input = data.get('user_input')
    page_content = data.get('page_content')
    
    logger.debug(f"Received chat query for: {user_input}")
    system_prompt = f"""You are a helpful assistant that answers questions based on 
        Hacker News webpages that will be provided to you in the Context field. 
        Use the provided context to answer questions accurately 
        and concisely. If you're not sure about something, say so. 
        
        Context: {page_content if page_content else ''}"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=500,
        stream=False
    )

    assistant_response = response.choices[0].message.content
    logger.debug(f"Assistant response: {assistant_response}")

    return jsonify({"bot_response": assistant_response})

# if __name__ == '__main__':
#     port = int(os.getenv('PORT', '8000'))
#     logger.info(f"Starting production server on 0.0.0.0:{port}")
#     serve(app, host='0.0.0.0', port=port)

if __name__ == '__main__':
  app.run(port=5000)