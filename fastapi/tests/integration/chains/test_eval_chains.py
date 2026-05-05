import pytest
from app.chains.eval_chains import response_eval_chain, code_eval_chain
from app.models import ResponseEvalResult, CodeEvalResult


class TestResponseEvalChain:
    """对话质量评估链测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_dialogue_quality_evaluation(self):
        """测试对话质量评估"""
        result = await response_eval_chain.ainvoke({
            "user_content": "评分最高的电影是哪部",
            "ai_response": "评分最高的电影是《肖申克的救赎》，IMDB评分为9.3分。"
        })
        assert result is not None
        assert isinstance(result.score, int)
        assert 1 <= result.score <= 5

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_json_output(self):
        """测试JSON输出"""
        result = await response_eval_chain.ainvoke({
            "user_content": "推荐几部动作片",
            "ai_response": "推荐《速度与激情》系列和《碟中谍》系列。"
        })
        assert isinstance(result, ResponseEvalResult)
        assert hasattr(result, "score")
        assert hasattr(result, "dimensions")
        assert hasattr(result, "issues")
        assert hasattr(result, "verdict")
        assert result.verdict in ["pass", "review", "fail"]


class TestCodeEvalChain:
    """代码质量评估链测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_code_quality_evaluation(self):
        """测试代码质量评估"""
        result = await code_eval_chain.ainvoke({
            "question": "绘制票房柱状图",
            "code": "from pyecharts.charts import Bar\nchart = Bar()\nchart.add_xaxis(['电影A', '电影B'])\nchart.add_yaxis('票房', [100, 200])",
            "exec_result": '{"success": true, "error": ""}'
        })
        assert result is not None
        assert isinstance(result.score, int)
        assert 1 <= result.score <= 5

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_json_output(self):
        """测试JSON输出"""
        result = await code_eval_chain.ainvoke({
            "question": "绘制评分分布图",
            "code": "from pyecharts.charts import Bar\nchart = Bar()\nchart.add_xaxis(['高分', '中分', '低分'])\nchart.add_yaxis('数量', [50, 30, 20])",
            "exec_result": '{"success": true, "error": ""}'
        })
        assert isinstance(result, CodeEvalResult)
        assert hasattr(result, "score")
        assert hasattr(result, "dimensions")
        assert hasattr(result, "issues")
        assert hasattr(result, "verdict")
