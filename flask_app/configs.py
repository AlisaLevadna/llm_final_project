import os
import dotenv

current_module_dir = os.path.dirname(__file__)
dotenv.load_dotenv(f"{current_module_dir}/.env", override=True)


REDIS_URL=os.environ["REDIS_URL"]
OPENAI_API_KEY= os.environ["OPENAI_API_KEY"]
