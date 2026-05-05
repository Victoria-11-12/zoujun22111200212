import pytest
from app.chains.chart_chains import chart_intent_chain, chart_not_chain, python_chart_chain


class TestChartIntentChain:
    """图表意图分类链测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_chart_intent_judgment(self):
        """测试绘图意图判断"""
        result = await chart_intent_chain.ainvoke({"question": "帮我绘制2013年电影的票房趋势图"})
        result = result.strip().upper()
        assert "IN_CHART" in result, f"绘图请求应返回 IN_CHART，实际返回: {result}"


class TestChartNotChain:
    """非图表请求链测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_non_chart_request_reply(self):
        """测试非绘图请求回复"""
        result = await chart_not_chain.ainvoke({"question": "你好"})
        assert result is not None
        assert len(result.strip()) > 0


class TestPythonChartChain:
    """Python图表生成链测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_python_code_generation(self):
        """测试Python代码生成"""
        result = await python_chart_chain.ainvoke({
            "question": "绘制2013年电影的票房柱状图",
            "data": "[{'movie_title': '电影A', 'gross': 500000}]",
            "feedback": ""
        })
        assert result is not None
        assert len(result.strip()) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_format_specification(self):
        """测试格式规范"""
        result = await python_chart_chain.ainvoke({
            "question": "绘制2013年电影的票房柱状图",
            "data": "[{'movie_title': '电影A', 'gross': 500000}]",
            "feedback": ""
        })
        assert "```python" in result or "pyecharts" in result, "生成代码应包含pyecharts"
        assert "CHART_HTML" in result, "生成代码应包含 CHART_HTML 变量"
