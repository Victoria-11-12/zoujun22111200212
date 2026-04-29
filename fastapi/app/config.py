import os

# Windows Docker 连接配置，必须在 import docker 之前设置
os.environ['DOCKER_HOST'] = 'npipe:////./pipe/docker_engine'

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
import pymysql

load_dotenv()

# 一、llm和数据库初始化

#llm模型初始化
#兼容openAI的模型
llm = ChatOpenAI(
    model=os.getenv('MODEL_NAME'),
    openai_api_key=os.getenv('API_KEY'),
    openai_api_base=os.getenv('API_BASE'),
    temperature=0.1,  #模型温度，0-1之间，越大越随机，越小越确定
    extra_body={"thinking": {"type": "disabled"}}  # 禁用思考模式
)

#数据库初始化
# mysql+pymysql:// - 数据库驱动协议，pymysql 是 Python 连接 MySQL 的库
#这里的管理员的root权限，拥有所有数据库的权限，包括创建、删除、修改、查询等
#注意环境变量的字段名要和.env文件中的字段名一致，否则会报错
#DB_USER_READONLY和DB_PASS_READONLY是可选的，如果不配置，默认使用DB_USER和DB_PASS连接
DB_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
db = SQLDatabase.from_uri(DB_URI)

# 普通用户使用只读数据库连接
DB_URI_READONLY = f"mysql+pymysql://{os.getenv('DB_USER_READONLY')}:{os.getenv('DB_PASS_READONLY')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
db_user = SQLDatabase.from_uri(DB_URI_READONLY, include_tables=['movies'])

# 管理员使用完全权限数据库连接
DB_URI_ADMIN = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"

print(f"数据库连接成功，可用表: {db.get_usable_table_names()}")

#日志处理
#数据库中要保存的模型名称，用于评估模型回复质量
#因为使用的模型名称都是一样的，所以这里直接从环境变量获取
MODEL_NAME = os.getenv('MODEL_NAME')
