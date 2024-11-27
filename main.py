from flask import Flask, request, jsonify
from flask_cors import CORS 
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

os.environ["EXA_API_URL"] = "https://api.exa.ai"
EXA_API_URL = os.getenv("EXA_API_URL")
EXA_API_KEY = os.getenv("EXA_API_KEY")
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = Flask(__name__)
CORS(app)  

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
        return jsonify({"results": response.json()})
    except requests.exceptions.RequestException as e:
        print(f"Error details: {str(e)}")
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
        print(f"Response status: {response.status_code}")
        response.raise_for_status()
        return jsonify({"content": response.json()})
    except requests.exceptions.RequestException as e:
        print(f"Error details: {str(e)}")
        return jsonify({
            "error": f"Error communicating with EXA Content API: {str(e)}"
        }), 500

@app.route("/query_exa_chat", methods=['POST'])
def chat_exa():
    data = request.get_json()
    user_input = data.get('user_input')
    page_content = data.get('page_content')
    
    print(f"Received chat query for: {user_input}")
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
    print(f"Assistant response: {assistant_response}")

    return jsonify({"bot_response": assistant_response})

if __name__ == '__main__':
    app.run(debug=True, port=8000)