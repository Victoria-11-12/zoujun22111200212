"""
API测试Fixtures
提供FastAPI测试客户端和请求模拟
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from main import app


@pytest.fixture(scope="module")
def client():
    """
    模块级同步测试客户端
    用于同步API测试
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
async def async_client():
    """
    模块级异步测试客户端
    用于异步API测试和流式响应测试
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_chat_request():
    """
    标准聊天请求fixture
    """
    return {
        "message": "查询电影信息",
        "sessionId": "test_session_001",
        "username": "test_user",
        "clientIp": "127.0.0.1"
    }


@pytest.fixture
def sample_admin_request():
    """
    管理员请求fixture
    """
    return {
        "message": "查询所有用户",
        "sessionId": "admin_session_001",
        "username": "admin",
        "clientIp": "127.0.0.1"
    }


@pytest.fixture
def sample_chart_request():
    """
    图表生成请求fixture
    """
    return {
        "message": "绘制电影评分分布图",
        "sessionId": "chart_session_001",
        "username": "test_user"
    }
