"""
E2E测试 - 质量评估接口
测试 /api/analyst/* 的完整HTTP请求/响应流程
"""
import pytest


class TestAnalystEndpoints:

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_start_eval_task(self, async_client):
        payload = {
            "tables": ["user_chat_logs", "admin_chat_logs", "chart_generation_logs", "security_warning_logs"],
            "start_date": "",
            "end_date": ""
        }
        response = await async_client.post("/api/analyst/evaluate", json=payload)
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("application/json")
        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_get_eval_progress(self, async_client):
        response = await async_client.get("/api/analyst/evaluate/progress")
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("application/json")
        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_query_eval_results(self, async_client):
        payload = {
            "table": "user_chat_logs",
            "start_time": None,
            "end_time": None
        }
        response = await async_client.post("/api/analyst/query", json=payload)
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("application/json")
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_get_results_stats(self, async_client):
        response = await async_client.get("/api/analyst/results", params={"min_score": 0})
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("application/json")
        data = response.json()
        assert isinstance(data, dict)
