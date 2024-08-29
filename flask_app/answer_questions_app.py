

import os
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings
from llama_index.vector_stores.redis import RedisVectorStore
from redis import Redis
from llama_index.core import VectorStoreIndex
from redisvl.schema import IndexSchema
from flask import Flask, request, Response, current_app



app = Flask(__name__)
app.config.from_pyfile("configs.py")

slack_app = App(token=app.config["SLACK_BOT_TOKEN"])
print("starting")
socket_mode_handler = SocketModeHandler(slack_app, app.config["SLACK_APP_TOKEN"])


# Settings.llm = Ollama(model="llama3.1:latest", request_timeout=120.0, base_url=app.config["MODEL_BASE_URL"]) # for local ollama model
# Settings.embed_model =  OllamaEmbedding(
#     model_name="nomic-embed-text",
#     base_url=app.config["EMBEDDING_MODEL_BASE_URL"],
# )
Settings.embed_model = OpenAIEmbedding(model="text-embedding-ada-002") # for OpenAI embedding

def get_query_engine():
        redis_client = Redis.from_url(app.config["REDIS_URL"])
        vector_store = RedisVectorStore(
            schema=IndexSchema.from_yaml("redis_schema.yaml"),
            redis_client=redis_client,
        )
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        query_engine = index.as_query_engine()
        return query_engine

# Event listener for the Slack bot
@slack_app.event("app_mention") 
def handle_app_mention_events(body, say):
    text = body['event']['text']
    print(text)
    if "search" in text.lower():
        query_engine = get_query_engine()
        response = query_engine.query(text)
        say(response.response)  # Assuming response 


@app.route("/query", methods=["POST"])
def query():
    content = request.get_json()
    question = content["question"]
    print(question)
    query_engine = get_query_engine()
    response = query_engine.query(question)
    print(response)
    return Response(json.dumps({"response": str(response)}), status=200)


socket_mode_handler.start() #comment out if you just need to send requests to an endpoint without slack