import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase

load_dotenv()

# LLM模型初始化
llm = ChatOpenAI(
    model=os.getenv('MODEL_NAME'),
    openai_api_key=os.getenv('API_KEY'),
    openai_api_base=os.getenv('API_BASE'),
    temperature=0.1,
    extra_body={"thinking": {"type": "disabled"}}
)

# 数据库连接配置
DB_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
db = SQLDatabase.from_uri(DB_URI)

# 只读数据库连接
DB_URI_READONLY = f"mysql+pymysql://{os.getenv('DB_USER_READONLY')}:{os.getenv('DB_PASS_READONLY')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
db_user = SQLDatabase.from_uri(DB_URI_READONLY, include_tables=['movies'])

# 全局配置
MODEL_NAME = os.getenv('MODEL_NAME')
MAX_HISTORY = 10

print(f"数据库连接成功，可用表: {db.get_usable_table_names()}")
