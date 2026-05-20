import os
import sys

from dotenv import load_dotenv
load_dotenv()

# Windows Docker 连接配置，必须在 import os
if sys.platform == 'win32':
    os.environ['DOCKER_HOST'] = 'npipe:////./pipe/docker_engine'

from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
import pymysql
import httpx

# 自定义 httpx 客户端，调大连接池避免密集调用时连接复用失败
# 同步客户端用于同步调用
_http_client = httpx.Client(
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=40, keepalive_expiry=30),
    timeout=httpx.Timeout(60.0, connect=30.0)
)
# 异步客户端用于异步调用
# keepalive_expiry 设短，使空闲连接在测试事件循环关闭前自动回收
_http_async_client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=40, keepalive_expiry=10),
    timeout=httpx.Timeout(60.0, connect=30.0)
)

#llm模型初始化
#兼容openAI的模型
llm = ChatOpenAI(
    model=os.getenv('MODEL_NAME'),
    openai_api_key=os.getenv('API_KEY'),
    openai_api_base=os.getenv('API_BASE'),
    temperature=0.1,  #模型温度，0-1之间，越大越随机，越小越确定
    streaming=True,
    stream_usage=True,  # 流式调用时返回 token 用量
    extra_body={"thinking": {"type": "disabled"}},  # 禁用思考模式
    http_client=_http_client,
    http_async_client=_http_async_client
)

#数据库初始化
# mysql+pymysql:// - 数据库驱动协议，pymysql 是 Python 连接 MySQL 的库
#这里的管理员的root权限，拥有所有数据库的权限，包括创建、删除、修改、查询等
#注意环境变量的字段名要和.env文件中的字段名一致，否则会报错
#DB_USER_READONLY和DB_PASS_READONLY是可选的，如果不配置，默认使用DB_USER和DB_PASS连接
# 管理员使用完全权限数据库连接
DB_URI_ADMIN = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}"
db = SQLDatabase.from_uri(DB_URI_ADMIN)

# 全局数据库连接池（管理员权限）
# pool_size: 连接池保持的连接数
# max_overflow: 超出pool_size后最多创建的连接数
# pool_recycle: 连接回收时间（秒），避免MySQL连接超时
engine = create_engine(DB_URI_ADMIN, pool_size=10, max_overflow=20, pool_recycle=3600)

# 普通用户使用只读数据库连接
DB_URI_READONLY = f"mysql+pymysql://{os.getenv('DB_USER_READONLY')}:{os.getenv('DB_PASS_READONLY')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}"
db_user = SQLDatabase.from_uri(DB_URI_READONLY, include_tables=['movies'])

# 全局数据库连接池（只读权限）
engine_readonly = create_engine(DB_URI_READONLY, pool_size=5, max_overflow=10, pool_recycle=3600)

print(f"数据库连接成功，可用表: {db.get_usable_table_names()}")

#日志处理
#数据库中要保存的模型名称，用于评估模型回复质量
#因为使用的模型名称都是一样的，所以这里直接从环境变量获取
MODEL_NAME = os.getenv('MODEL_NAME')

# 评估模块专用 LLM
eval_llm = ChatOpenAI(
    model=os.getenv('EVAL_MODEL_NAME'),
    api_key=os.getenv('EVAL_API_KEY'),
    base_url=os.getenv('API_BASE'),
    temperature=0,
    http_client=_http_client,
    http_async_client=_http_async_client
)

# 分析师数据库连接（只读权限，用于质量评估）
DB_USER_ANALYST = os.getenv('DB_USER_ANALYST')
DB_PASS_ANALYST = os.getenv('DB_PASS_ANALYST')
DB_URI_ANALYST = f"mysql+pymysql://{DB_USER_ANALYST}:{DB_PASS_ANALYST}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}"

# 全局数据库连接池（分析师只读权限）
engine_analyst = create_engine(DB_URI_ANALYST, pool_size=5, max_overflow=10, pool_recycle=3600)
