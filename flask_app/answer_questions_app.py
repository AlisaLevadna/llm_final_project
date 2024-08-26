

import os
import json
from llama_index.vector_stores.redis import RedisVectorStore
from redis import Redis
from llama_index.core import VectorStoreIndex
from redisvl.schema import IndexSchema


from flask import Flask, request, Response, current_app

app = Flask(__name__)
app.config.from_pyfile("configs.py")

def get_query_engine():
        redis_client = Redis.from_url(app.config["REDIS_URL"])
        vector_store = RedisVectorStore(
            schema=IndexSchema.from_yaml("redis_schema.yaml"),
            redis_client=redis_client,
        )
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        query_engine = index.as_query_engine()
        return query_engine

@app.route("/query", methods=["POST"])
def query():
    content = request.get_json()
    question = content["question"]
    print(question)
    query_engine = get_query_engine()
    response = query_engine.query(question)
    print(response)
    return Response(json.dumps({"response": str(response)}), status=200)


if __name__ == "__main__":
    with app.app_context():
        current_app.query_engine = get_query_engine()
    app.run()