from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
from typing import Optional  
from openai import OpenAI

load_dotenv()

os.environ["EXA_API_URL"] = "https://api.exa.ai"
EXA_API_URL = os.getenv("EXA_API_URL")
EXA_API_KEY = os.getenv("EXA_API_KEY")
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

class Query(BaseModel):
    user_input: str
    page_content: Optional[str] = None

@app.post("/query_exa_search")
def query_exa_search(query: Query):
    headers = {"x-api-key": EXA_API_KEY,"Content-Type": "application/json"}
    payload = {"query": query.user_input, "numResults": 6, "includeDomains": ["news.ycombinator.com/"],}

    try:
        response = requests.post(EXA_API_URL+"/search", headers=headers, json=payload)
        
        response.raise_for_status()
        return {"results": response.json()}
    except requests.exceptions.RequestException as e:
        print(f"Error details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with EXA API: {str(e)}"
        )

@app.post("/query_exa_content")
def query_exa_content(query: Query):
    headers = {"x-api-key": EXA_API_KEY,"Content-Type": "application/json"}
    payload = {"ids": [query.user_input]}

    try:
        response = requests.post(EXA_API_URL+"/contents", headers=headers, json=payload)
        print(f"Response status: {response.status_code}")
        response.raise_for_status()
        return {"content": response.json()}
    except requests.exceptions.RequestException as e:
        print(f"Error details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with EXA Content API: {str(e)}"
        )
    
@app.post("/query_exa_chat")
def chat_exa(query: Query):
    print(f"Received chat query for: {query.user_input}")
    system_prompt = f"""You are a helpful assistant that answers questions based on 
        Hacker News webpages that will be provided to you in the Context field. 
        Use the provided context to answer questions accurately 
        and concisely. If you're not sure about something, say so. 
        
        Context: {query.page_content if query.page_content else ''}""" 
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query.user_input}
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

    return {"bot_response": assistant_response}