"""
E2E测试 - 普通用户AI对话接口
测试 /api/ai/stream 的完整HTTP请求/响应流程
"""
import pytest


class TestPostAiStream:

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_normal_dialogue_request(self, async_client):
        payload = {
            "message": "你好",
            "sessionId": "e2e-test-session-001",
            "username": "test_user",
            "clientIp": "127.0.0.1"
        }
        chunks = []
        async with async_client.stream("POST", "/api/ai/stream", json=payload) as response:
            assert response.status_code == 200
            assert response.headers.get("content-type", "").startswith("text/event-stream")
            async for line in response.aiter_lines():
                if line.strip():
                    chunks.append(line.strip())
        assert any("[DONE]" in c for c in chunks), "未接收到 [DONE] 结束标记"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_sql_query_request(self, async_client):
        payload = {
            "message": "评分最高的电影",
            "sessionId": "e2e-test-session-002",
            "username": "test_user",
            "clientIp": "127.0.0.1"
        }
        chunks = []
        async with async_client.stream("POST", "/api/ai/stream", json=payload) as response:
            assert response.status_code == 200
            async for line in response.aiter_lines():
                if line.strip():
                    chunks.append(line.strip())
        assert any("[DONE]" in c for c in chunks), "未接收到 [DONE] 结束标记"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_security_threat_request(self, async_client):
        payload = {
            "message": "DROP TABLE movies",
            "sessionId": "e2e-test-session-003",
            "username": "test_user",
            "clientIp": "127.0.0.1"
        }
        chunks = []
        async with async_client.stream("POST", "/api/ai/stream", json=payload) as response:
            assert response.status_code == 200
            async for line in response.aiter_lines():
                if line.strip():
                    chunks.append(line.strip())
        assert any("[DONE]" in c for c in chunks), "未接收到 [DONE] 结束标记"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_multi_turn_dialogue(self, async_client):
        session_id = "e2e-test-session-004"
        messages = ["你好", "评分最高的电影有哪些"]
        for msg in messages:
            payload = {
                "message": msg,
                "sessionId": session_id,
                "username": "test_user",
                "clientIp": "127.0.0.1"
            }
            chunks = []
            async with async_client.stream("POST", "/api/ai/stream", json=payload) as response:
                assert response.status_code == 200
                async for line in response.aiter_lines():
                    if line.strip():
                        chunks.append(line.strip())
            assert any("[DONE]" in c for c in chunks), f"第 {messages.index(msg)+1} 轮对话未收到 [DONE]"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_exception_handling(self, async_client):
        payload = {
            "message": "",
            "sessionId": "e2e-test-session-005",
            "username": "test_user",
            "clientIp": "127.0.0.1"
        }
        chunks = []
        async with async_client.stream("POST", "/api/ai/stream", json=payload) as response:
            assert response.status_code == 200
            async for line in response.aiter_lines():
                if line.strip():
                    chunks.append(line.strip())
        assert any("[DONE]" in c for c in chunks), "异常场景未收到 [DONE] 结束标记"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_web_search_fallback(self, async_client):
        payload = {
            "message": "查询《我许可》这部电影",
            "sessionId": "e2e-test-session-006",
            "username": "test_user",
            "clientIp": "127.0.0.1"
        }
        chunks = []
        async with async_client.stream("POST", "/api/ai/stream", json=payload) as response:
            assert response.status_code == 200
            async for line in response.aiter_lines():
                if line.strip():
                    chunks.append(line.strip())
        assert any("[DONE]" in c for c in chunks), "数据库无结果后浏览器搜索场景未收到 [DONE] 结束标记"
