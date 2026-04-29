# SQL查询工具
# 用于查询本地MySQL数据库中的电影信息

from langchain.tools import tool
from app.config import db_user


@tool
def sql_db_query(query: str) -> str:
    """执行 SQL 查询语句，输入完整的 SQL 语句"""
    return db_user.run(query)
