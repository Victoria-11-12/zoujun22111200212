"""
E2E测试Fixtures
提供E2E级别测试所需的HTTP客户端
"""
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
async def async_client():
    """
    异步HTTP客户端
    直接连接FastAPI应用，发送真实HTTP请求
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
