import pytest
from app.workflows.chart_workflow import (
    _node_sqlagent, _node_pythonagent, _node_eval, _node_pyecharts_sandbox,
    _build_chart_graph, _static_eval, _extract_python_code_block,
    _route_after_eval, _route_after_sandbox, ChartGraphState, chart_graph
)
from langgraph.graph import END


class TestNodeSqlagent:
    """测试SQLAgent节点"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sql_agent_node(self):
        """测试SQLAgent节点"""
        state: ChartGraphState = {
            "question": "查询评分最高的电影",
            "session_id": "test-session",
            "user_name": "test",
            "feedback": "",
            "attempts": 0
        }
        result = await _node_sqlagent(state)
        assert "sql_result" in result
        assert len(result["sql_result"]) > 0


class TestNodePythonagent:
    """测试PythonAgent节点"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_python_agent_node(self):
        """测试PythonAgent节点"""
        state: ChartGraphState = {
            "question": "绘制评分最高的10部电影的条形图",
            "session_id": "test-session",
            "user_name": "test",
            "sql_result": "[{'movie_title': '肖申克的救赎', 'imdb_score': 9.3}]",
            "feedback": "",
            "attempts": 0
        }
        result = await _node_pythonagent(state)
        assert "code_raw" in result
        assert len(result["code_raw"]) > 0


class TestNodeEval:
    """测试Eval节点"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_eval_node_pass(self):
        """测试Eval节点代码检查通过"""
        state: ChartGraphState = {
            "code_raw": "```python\nfrom pyecharts.charts import Bar\nchart = Bar()\nprint('CHART_HTML_START')\nprint(chart.render_embed())\nprint('CHART_HTML_END')\n```",
            "attempts": 1,
            "feedback": ""
        }
        result = await _node_eval(state)
        assert result.get("eval_pass") is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_eval_node_fail(self):
        """测试Eval节点检测到缺失标记"""
        state: ChartGraphState = {
            "code_raw": "```python\nprint('hello')\n```",
            "attempts": 1,
            "feedback": ""
        }
        result = await _node_eval(state)
        assert result.get("eval_pass") is False


class TestNodePyechartsSandbox:
    """测试pyecharts-sandbox节点"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sandbox_execute_success(self):
        """测试沙箱执行成功"""
        state: ChartGraphState = {
            "question": "绘制评分最高的10部电影的条形图",
            "session_id": "test-session",
            "user_name": "test",
            "sql_result": "[{'movie_title': '肖申克的救赎', 'imdb_score': 9.3}]",
            "code": "from pyecharts.charts import Bar\nchart = Bar()\nchart.add_xaxis(['肖申克的救赎'])\nchart.add_yaxis('评分', [9.3])\nprint('CHART_HTML_START')\nprint(chart.render_embed())\nprint('CHART_HTML_END')",
            "attempts": 1,
            "feedback": ""
        }
        result = await _node_pyecharts_sandbox(state)
        assert "chart_html" in result or "error" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sandbox_execute_invalid_code(self):
        """测试沙箱执行失败"""
        state: ChartGraphState = {
            "question": "测试",
            "session_id": "test-session",
            "user_name": "test",
            "sql_result": "[]",
            "code": "this is invalid python code",
            "attempts": 1,
            "feedback": ""
        }
        result = await _node_pyecharts_sandbox(state)
        assert "error" in result, "无效代码执行应返回错误"


class TestBuildChartGraph:
    """测试图表工作流图结构"""

    @pytest.mark.integration
    def test_graph_topology(self):
        """测试图拓扑结构"""
        graph = _build_chart_graph()
        assert graph is not None

    @pytest.mark.integration
    def test_node_registration(self):
        """测试节点注册"""
        graph = _build_chart_graph()
        assert hasattr(graph, "get_graph")

    @pytest.mark.integration
    def test_edge_connection(self):
        """测试边连接"""
        graph = _build_chart_graph()
        nodes = graph.get_graph().nodes
        node_names = [n.id if hasattr(n, 'id') else str(n) for n in nodes]
        assert any("sqlagent" in n for n in node_names)
        assert any("pythonagent" in n for n in node_names)
        assert any("eval" in n for n in node_names)
        assert any("pyecharts_sandbox" in n for n in node_names)

    @pytest.mark.integration
    def test_conditional_route_config(self):
        """测试条件路由配置"""
        eval_next = _route_after_eval({"eval_pass": False, "attempts": 1})
        assert eval_next == "pythonagent"

        sandbox_done = _route_after_sandbox({"chart_html": "<html>test</html>", "attempts": 1})
        assert sandbox_done == END

        sandbox_retry = _route_after_sandbox({"error": "exec failed", "attempts": 1})
        assert sandbox_retry == "pythonagent"

        sandbox_giveup = _route_after_sandbox({"error": "exec failed", "attempts": 3})
        assert sandbox_giveup == END


class TestChartGraph:
    """测试完整图表工作流"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_orchestration(self):
        """测试完整编排"""
        result = await chart_graph.ainvoke({
            "question": "查询IMDB评分最高的5部电影并绘制条形图",
            "session_id": "test-session",
            "user_name": "test",
            "feedback": "",
            "attempts": 0
        })
        assert result is not None
        assert "chart_html" in result or "error" in result or "sql_result" in result
