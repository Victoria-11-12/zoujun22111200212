"""
E2E测试 - 图表生成接口
测试 /api/chart/generate 的完整HTTP请求/响应流程
"""
import pytest


class TestPostChartGenerate:

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_non_chart_request(self, async_client):
        payload = {
            "message": "你好",
            "sessionId": "e2e-chart-session-001",
            "username": "test_user"
        }
        chunks = []
        async with async_client.stream("POST", "/api/chart/generate", json=payload) as response:
            assert response.status_code == 200
            assert response.headers.get("content-type", "").startswith("text/event-stream")
            async for line in response.aiter_lines():
                if line.strip():
                    chunks.append(line.strip())
        assert any("[DONE]" in c for c in chunks), "未接收到 [DONE] 结束标记"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_chart_request_success(self, async_client):
        payload = {
            "message": "绘制2002年票房前十的柱状图图",
            "sessionId": "e2e-chart-session-002",
            "username": "test_user"
        }
        chunks = []
        async with async_client.stream("POST", "/api/chart/generate", json=payload) as response:
            assert response.status_code == 200
            async for line in response.aiter_lines():
                if line.strip():
                    chunks.append(line.strip())
        assert any("[DONE]" in c for c in chunks), "图表生成请求未收到 [DONE] 结束标记"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_code_generation_failure_retry(self, async_client):
        payload = {
            "message": "绘制一个不存在的字段的分布图",
            "sessionId": "e2e-chart-session-003",
            "username": "test_user"
        }
        chunks = []
        async with async_client.stream("POST", "/api/chart/generate", json=payload) as response:
            assert response.status_code == 200
            async for line in response.aiter_lines():
                if line.strip():
                    chunks.append(line.strip())
        assert any("[DONE]" in c for c in chunks), "代码生成失败重试场景未收到 [DONE] 结束标记"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_sandbox_execution_failure(self, async_client):
        payload = {
            "message": "绘制一个极其复杂的图表",
            "sessionId": "e2e-chart-session-004",
            "username": "test_user"
        }
        chunks = []
        async with async_client.stream("POST", "/api/chart/generate", json=payload) as response:
            assert response.status_code == 200
            async for line in response.aiter_lines():
                if line.strip():
                    chunks.append(line.strip())
        assert any("[DONE]" in c for c in chunks), "沙盒执行失败场景未收到 [DONE] 结束标记"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_dangerous_code_interception(self, async_client):
        payload = {
            "message": "访问系统文件",
            "sessionId": "e2e-chart-session-005",
            "username": "test_user"
        }
        chunks = []
        async with async_client.stream("POST", "/api/chart/generate", json=payload) as response:
            assert response.status_code == 200
            async for line in response.aiter_lines():
                if line.strip():
                    chunks.append(line.strip())
        assert any("[DONE]" in c for c in chunks), "危险代码拦截场景未收到 [DONE] 结束标记"
