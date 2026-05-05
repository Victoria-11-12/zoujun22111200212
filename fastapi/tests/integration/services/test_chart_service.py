import pytest
import json
from app.chains.chart_chains import chart_intent_chain, chart_not_chain
from app.workflows.chart_workflow import chart_graph


class TestChartGenerate:
    """图表生成服务测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_intent_judgment(self):
        """测试图表意图判断"""
        intent = await chart_intent_chain.ainvoke({"question": "绘制2013年电影的票房趋势图"})
        intent = intent.strip().upper()
        assert "IN_CHART" in intent, f"绘图请求应返回 IN_CHART，实际返回: {intent}"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_call(self):
        """测试工作流调用"""
        result = await chart_graph.ainvoke({
            "question": "查询IMDB评分最高的5部电影并绘制条形图",
            "session_id": "test-chart-001",
            "user_name": "test",
            "feedback": "",
            "attempts": 0
        })
        assert result is not None
        assert "chart_html" in result or "error" in result or "sql_result" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_non_chart_response(self):
        """测试非绘图请求响应"""
        reply = await chart_not_chain.ainvoke({"question": "你好"})
        assert reply is not None
        assert len(reply.strip()) > 0
