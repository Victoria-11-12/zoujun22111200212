import pytest
from app.chains.user_chains import intent_chain, direct_chain, wrap_chain, warning_chain
from langchain_core.messages import HumanMessage, AIMessage


class TestIntentChain:
    """意图分类链测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_intent_classification_accuracy(self):
        """测试意图分类准确性"""
        result = await intent_chain.ainvoke({"message": "帮我查询评分最高的电影有哪些"})
        result = result.strip().upper()
        assert "NEED_SQL" in result, f"需要SQL查询的问题应返回 NEED_SQL，实际返回: {result}"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_safety_detection(self):
        """测试安全检测"""
        result = await intent_chain.ainvoke({"message": "DROP TABLE movies"})
        result = result.strip().upper()
        assert "WARNING" in result, f"危险操作应返回 WARNING，实际返回: {result}"


class TestDirectChain:
    """直接回复链测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_direct_reply_generation(self):
        """测试直接回复生成"""
        result = await direct_chain.ainvoke({"message": "你好", "history": []})
        assert result is not None
        assert len(result.strip()) > 0, "直接回复不能为空"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_history_context(self):
        """测试历史上下文"""
        history = [
            HumanMessage(content="推荐几部好看的电影"),
            AIMessage(content="推荐《泰坦尼克号》、《盗梦空间》和《星际穿越》")
        ]
        result = await direct_chain.ainvoke({"message": "能详细说说第二部吗", "history": history})
        assert result is not None
        assert len(result.strip()) > 0, "带历史上下文的回复不能为空"


class TestWrapChain:
    """包装链测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sql_result_wrapping(self):
        """测试SQL结果包装"""
        result = await wrap_chain.ainvoke({
            "question": "评分最高的电影是哪部",
            "result": "[{'movie_title': '肖申克的救赎', 'imdb_score': 9.3}]",
            "history": []
        })
        assert result is not None
        assert len(result.strip()) > 0, "SQL结果包装回复不能为空"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_natural_language_generation(self):
        """测试自然语言生成"""
        result = await wrap_chain.ainvoke({
            "question": "2015年上映的电影有哪些",
            "result": "[{'movie_title': '火星救援', 'title_year': 2015}]",
            "history": []
        })
        assert result is not None
        assert len(result.strip()) > 0


class TestWarningChain:
    """警告链测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_warning_reply_generation(self):
        """测试警告回复生成"""
        result = await warning_chain.ainvoke({"message": "DROP TABLE movies"})
        assert result is not None
        assert len(result.strip()) > 0
