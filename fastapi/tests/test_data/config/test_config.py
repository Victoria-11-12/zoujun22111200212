"""
测试配置文件
定义测试环境和参数
"""
import os

TEST_DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3307")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", "test123"),
    "database": os.getenv("DB_NAME", "movie_test"),
}

TEST_API_CONFIG = {
    "api_key": os.getenv("API_KEY"),
    "model_name": os.getenv("MODEL_NAME"),
    "api_base": os.getenv("API_BASE"),
}

TEST_TABLES = [
    "user_chat_logs",
    "admin_chat_logs", 
    "chart_generation_logs",
    "security_warning_logs",
    "users",
    "movies",
    "rollback_logs",
]

MAX_HISTORY = 10
MAX_TEST_ITERATIONS = 3
