"""
数据库测试Fixtures
提供测试数据库连接和会话管理
"""
import pytest
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import engine


@pytest.fixture(scope="function")
def db_connection():
    """
    函数级数据库连接fixture
    每个测试函数获取独立连接，测试结束后自动关闭
    """
    conn = engine.raw_connection()
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def db_cursor(db_connection):
    """
    函数级数据库游标fixture
    自动获取连接并创建游标
    """
    cursor = db_connection.cursor()
    yield cursor
    cursor.close()


@pytest.fixture(scope="function")
def clean_users_table(db_cursor):
    """
    清理users表的fixture
    测试前备份，测试后恢复
    """
    db_cursor.execute("SELECT * FROM users")
    backup = db_cursor.fetchall()
    yield
    db_cursor.execute("DELETE FROM users")
    if backup:
        for row in backup:
            db_cursor.execute(
                "INSERT INTO users (id, username, password, role, created_at) VALUES (%s, %s, %s, %s, %s)",
                row
            )
    db_cursor.connection.commit()


@pytest.fixture(scope="function")
def clean_chat_logs(db_cursor):
    """
    清理聊天日志表的fixture
    """
    tables = ["user_chat_logs", "admin_chat_logs", "chart_generation_logs", "security_warning_logs"]
    for table in tables:
        db_cursor.execute(f"DELETE FROM {table}")
    db_cursor.connection.commit()
    yield
