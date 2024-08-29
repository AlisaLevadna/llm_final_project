#!/usr/bin/env python
# coding: utf-8

# In[9]:



# In[18]:


import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from llama_index.readers.google import GoogleDriveReader
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.redis import RedisVectorStore
from redis import Redis 
from redisvl.schema import IndexSchema
import os
import requests

from flask import Flask, app, jsonify, request, Response, current_app

# Flask app initialization
app_flask = Flask(__name__)
app_flask.config.from_pyfile("configs.py")

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]

SLACK_ENDPOINT_URL = "http://localhost:9090/query"  # Adjust this if the Flask app is running on a different port or domain

slack_app = App(token=SLACK_BOT_TOKEN)

# Google Drive Authentication and Document Loading
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

def authenticate_gdrive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def load_single_document(doc_id):
    creds = authenticate_gdrive()
    service = build('drive', 'v3', credentials=creds)
    loader = GoogleDriveReader()
    docs = loader.load_data(document_ids=[doc_id]) 
    return docs

def create_index(doc_id):
    google_docs = load_single_document(doc_id)
    index = VectorStoreIndex.from_documents(google_docs)
    return index.as_query_engine()

@app_flask.route('/slack/events', methods=['POST'])
def slack_events():
    data = request.json

    # Handling Slack's URL verification challenge
    if "challenge" in data:
        return jsonify({'challenge': data['challenge']})

    # Event handling logic
    if "event" in data:
        event_data = data["event"]
        if event_data.get("type") == "app_mention":
            text = event_data.get('text', '')
            if "search" in text.lower():
                question = text.split("search", 1)[1].strip()
                if question:
                    response = requests.post(SLACK_ENDPOINT_URL, json={"question": question})
                    if response.status_code == 200:
                        say_response = response.json().get("response", "I couldn't find an answer.")
                    else:
                        say_response = "There was an error processing your request."
                else:
                    say_response = "Please provide a question to search."
                # Assuming you have a method to send a message back to Slack
                send_message(event_data["channel"], say_response)

    return "OK", 200

def send_message(channel, text):
    slack_app.client.chat_postMessage(channel=channel, text=text)

# Flask app for handling query
def get_query_engine():
    redis_client = Redis.from_url(app_flask.config["REDIS_URL"])
    vector_store = RedisVectorStore(
        schema=IndexSchema.from_yaml("redis_schema.yaml"),
        redis_client=redis_client,
    )
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    query_engine = index.as_query_engine()
    return query_engine


@app_flask.route("/query", methods=["POST"])
def query():
    content = request.get_json()
    question = content["question"]
    print(question)
    query_engine = get_query_engine()
    response = query_engine.query(question)
    print(response)
    return Response(json.dumps({"response": str(response)}), status=200)

if __name__ == "__main__":
    # Start the Flask app
    app_flask.run(host="0.0.0.0", port=9090)
