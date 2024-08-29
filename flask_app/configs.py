import os
import dotenv

current_module_dir = os.path.dirname(__file__)
dotenv.load_dotenv(f"{current_module_dir}/.env", override=True)


REDIS_URL=os.environ["REDIS_URL"]
SLACK_APP_TOKEN=os.environ["SLACK_APP_TOKEN"]
SLACK_BOT_TOKEN=os.environ["SLACK_BOT_TOKEN"]
OPENAI_API_KEY= os.environ["OPENAI_API_KEY"]
EMBEDDING_MODEL_BASE_URL=os.environ["EMBEDDING_MODEL_BASE_URL"]
MODEL_BASE_URL=os.environ["MODEL_BASE_URL"]
