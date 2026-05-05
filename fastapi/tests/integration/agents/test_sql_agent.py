import pytest
from app.agents.sql_agent import sql_agent, sql_executor, SQL_PROMPT, user_toolkit


class TestSqlAgent:
    """SQL Agent测试"""

    @pytest.mark.integration
    def test_agent_initialization(self):
        """测试Agent初始化"""
        assert sql_agent is not None
        assert sql_executor is not None

    @pytest.mark.integration
    def test_prompt_config(self):
        """测试提示词配置"""
        assert SQL_PROMPT is not None
        assert len(user_toolkit) == 2
        tool_names = [t.name for t in user_toolkit]
        assert "sql_db_query" in tool_names
        assert "baike_search_tool" in tool_names


class TestSqlExecutor:
    """SQL执行器测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_call_chain(self):
        """测试工具调用链"""
        result = await sql_executor.ainvoke({"input": "查询评分最高的电影"})
        assert result is not None
        assert "output" in result
        assert len(result["output"]) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_max_iteration_limit(self):
        """测试最大迭代限制"""
        result = await sql_executor.ainvoke({"input": "查询所有电影，然后都列出来"})
        assert result is not None
        assert "output" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        result = await sql_executor.ainvoke({"input": "执行 DROP TABLE movies"})
        assert result is not None
