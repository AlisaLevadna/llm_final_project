from datetime import datetime, timedelta
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.decorators import dag, task
from airflow.utils.trigger_rule import TriggerRule
from airflow.utils.email import send_email
from airflow.models import Variable
from airflow.configuration import conf
import os
import json
from pathlib import Path
from typing import List, Dict, Any
import requests
from requests.auth import HTTPBasicAuth
import io
from googleapiclient.http import MediaIoBaseDownload
from llama_index.readers.google import GoogleDriveReader
# from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from llama_index.vector_stores.redis import RedisVectorStore

from redis import Redis

from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.ingestion import (
    DocstoreStrategy,
    IngestionPipeline,
    IngestionCache,
)
from llama_index.storage.kvstore.redis import RedisKVStore as RedisCache
from llama_index.storage.docstore.redis import RedisDocumentStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.redis import RedisVectorStore
from llama_index.core import Settings
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from redisvl.schema import IndexSchema



SCOPES = ['https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/documents.readonly',
          "https://www.googleapis.com/auth/spreadsheets.readonly",
          "https://www.googleapis.com/auth/drive.readonly"]


# Set default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

DAG_DIR = conf.get('core', 'DAGS_FOLDER')


def download_report(drive_service, id, name):
    os.makedirs(f"{DAG_DIR}/refresh_dag/files", exist_ok=True)
    request = drive_service.files().get_media(fileId=id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    with open(name, 'b+w') as f:
        f.write(fh.getbuffer())


def get_google_service():
    creds = None
    if os.path.exists(f"{DAG_DIR}/refresh_dag/tokens/{Variable.get('service_account_token')}"):
        creds = Credentials.from_service_account_file(f"{DAG_DIR}/refresh_dag/tokens/{Variable.get('service_account_token')}", scopes=SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

    service = build("drive", "v3", credentials=creds)
    return service


def load_data(folder_id: str, service):
    with open(f"{DAG_DIR}/refresh_dag/tokens/{Variable.get('service_account_token')}") as f:
        service_account_info = json.load(f)
    loader = GoogleDriveReader(service_account_key=service_account_info, folder_id=folder_id)
    print(loader.list_resources(folder_id=folder_id))
    docs = loader.load_data(folder_id=folder_id)
    print(docs)
    for doc in docs:
        parents = service.files().get(fileId=doc.metadata["file id"], fields='parents, name, id').execute()
        full_name = parents['name']
        parent = parents['parents'][0]
        while parent != folder_id:
            file = service.files().get(fileId=parent, fields='parents, name, id').execute()
            full_name = f"{file['name']}/{full_name}"
            parent = file['parents'][0]
        doc.id_ = full_name
        if doc.metadata['mime type'] not in ['application/vnd.google-apps.document', 'application/vnd.google-apps.spreadsheet']:
            download_report(service, doc.metadata["file id"], f"{DAG_DIR}/refresh_dag/files/{doc.metadata['file name']}")
    local_documents = []
    if os.path.exists(f"{DAG_DIR}/refresh_dag/files/") and len(os.listdir(f"{DAG_DIR}/refresh_dag/files/")) > 0:
        local_documents = SimpleDirectoryReader(f"{DAG_DIR}/refresh_dag/files/").load_data()
    return docs + local_documents

def create_pipeline(vector_store):
    cache = IngestionCache(
    cache=RedisCache.from_host_and_port(Variable.get("redis_host"), 6379),
    collection="redis_gdrive_cache",
)   
    # embed_model =  OllamaEmbedding(
    # model_name="nomic-embed-text",
    # base_url=Variable.get('embedding_base_url'),
    # ) # for local ollama embedding
    embed_model = OpenAIEmbedding(model="text-embedding-ada-002") # for OpenAI embedding
    # cache.clear() # if need to clear the document cache - run redis-cli FLUSHALL and then ucnomment this for one rum 
    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(),
            embed_model,
        ],
        docstore=RedisDocumentStore.from_host_and_port(
            Variable.get("redis_host"), 6379, namespace="document_store"
        ),
        vector_store=vector_store,
        cache=cache,
        docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE,
    )
    return pipeline

@dag(
    'refresh_redis_vector_store',
    default_args=default_args,
    start_date=datetime(2024, 8, 22),
    schedule='0 8 * * *',
    catchup=False,
)
def refresh_index():
    @task
    def load_new_documents() -> List[str]:
        os.environ['OPENAI_API_KEY'] = Variable.get('open_ai_secret_key')
        redis_client = Redis.from_url(f"redis://{Variable.get('redis_host')}:6379")
        print(f"{DAG_DIR}/configs/redis_schema.yaml")
        
        vector_store = RedisVectorStore(
            schema=IndexSchema.from_yaml(f"{DAG_DIR}/configs/redis_schema.yaml"),
            redis_client=redis_client,
        )
        docs = load_data(folder_id=Variable.get('folder_id'), service=get_google_service())
        print(docs)
        pipeline = create_pipeline(vector_store)
        nodes = pipeline.run(documents=docs)
        print(f"Ingested {len(nodes)} Nodes")
    
    load_new_documents()

        

refresh_index()
