"""
Mock对象Fixtures
提供LLM、数据库、外部服务的Mock对象
"""
import pytest
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def mock_llm_response():
    """
    Mock LLM响应fixture
    """
    mock_response = Mock()
    mock_response.content = "这是一个模拟的AI回复"
    return mock_response


@pytest.fixture
def mock_chat_openai(mock_llm_response):
    """
    Mock ChatOpenAI实例
    """
    with patch("app.config.llm") as mock_llm:
        mock_llm.invoke.return_value = mock_llm_response
        mock_llm.stream.return_value = iter([mock_llm_response])
        yield mock_llm


@pytest.fixture
def mock_db_connection():
    """
    Mock数据库连接
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = Mock(return_value=mock_conn)
    mock_conn.__exit__ = Mock(return_value=False)
    return mock_conn


@pytest.fixture
def mock_sql_database():
    """
    Mock SQLDatabase实例
    """
    with patch("app.config.db") as mock_db:
        mock_db.run.return_value = "SELECT * FROM movies LIMIT 5"
        yield mock_db


@pytest.fixture
def mock_subprocess():
    """
    Mock subprocess调用
    用于测试web_tools中的子进程命令
    """
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="命令执行成功",
            stderr="",
            returncode=0
        )
        yield mock_run
