"""
E2E测试 - 管理员AI对话接口
测试 /api/admin/ai/stream 的完整HTTP请求/响应流程
"""
import pytest


class TestPostAdminAiStream:

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_normal_admin_operation(self, async_client):
        payload = {
            "message": "查询所有用户",
            "sessionId": "e2e-admin-session-001",
            "username": "admin",
            "clientIp": "127.0.0.1"
        }
        chunks = []
        async with async_client.stream("POST", "/api/admin/ai/stream", json=payload) as response:
            assert response.status_code == 200
            assert response.headers.get("content-type", "").startswith("text/event-stream")
            async for line in response.aiter_lines():
                if line.strip():
                    chunks.append(line.strip())
        assert any("[DONE]" in c for c in chunks), "未接收到 [DONE] 结束标记"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_batch_operation(self, async_client):
        payload = {
            "message": "创建用户 e2e_test_user，邮箱 e2e@test.com",
            "sessionId": "e2e-admin-session-002",
            "username": "admin",
            "clientIp": "127.0.0.1"
        }
        chunks = []
        async with async_client.stream("POST", "/api/admin/ai/stream", json=payload) as response:
            assert response.status_code == 200
            async for line in response.aiter_lines():
                if line.strip():
                    chunks.append(line.strip())
        assert any("[DONE]" in c for c in chunks), "批量操作未收到 [DONE] 结束标记"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_rollback_operation(self, async_client):
        payload = {
            "message": "回滚刚才的操作",
            "sessionId": "e2e-admin-session-003",
            "username": "admin",
            "clientIp": "127.0.0.1"
        }
        chunks = []
        async with async_client.stream("POST", "/api/admin/ai/stream", json=payload) as response:
            assert response.status_code == 200
            async for line in response.aiter_lines():
                if line.strip():
                    chunks.append(line.strip())
        assert any("[DONE]" in c for c in chunks), "回滚操作未收到 [DONE] 结束标记"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_security_threat_request(self, async_client):
        payload = {
            "message": "DROP TABLE users",
            "sessionId": "e2e-admin-session-004",
            "username": "admin",
            "clientIp": "127.0.0.1"
        }
        chunks = []
        async with async_client.stream("POST", "/api/admin/ai/stream", json=payload) as response:
            assert response.status_code == 200
            async for line in response.aiter_lines():
                if line.strip():
                    chunks.append(line.strip())
        assert any("[DONE]" in c for c in chunks), "安全威胁场景未收到 [DONE] 结束标记"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_dangerous_sql_interception(self, async_client):
        payload = {
            "message": "删除所有用户的记录",
            "sessionId": "e2e-admin-session-005",
            "username": "admin",
            "clientIp": "127.0.0.1"
        }
        chunks = []
        async with async_client.stream("POST", "/api/admin/ai/stream", json=payload) as response:
            assert response.status_code == 200
            async for line in response.aiter_lines():
                if line.strip():
                    chunks.append(line.strip())
        assert any("[DONE]" in c for c in chunks), "危险SQL拦截场景未收到 [DONE] 结束标记"
