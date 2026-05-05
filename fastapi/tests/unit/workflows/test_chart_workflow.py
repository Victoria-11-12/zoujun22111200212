import pytest
from app.workflows.chart_workflow import (
    ChartGraphState,
    _extract_python_code_block,
    _static_eval,
    _route_after_eval,
    _route_after_sandbox,
)
from langgraph.graph import END


class TestChartGraphState:
    """图表工作流状态测试"""

    @pytest.mark.unit
    def test_state_definition(self):
        """测试状态定义"""
        # 验证ChartGraphState是TypedDict类型
        # 创建一个状态实例
        state: ChartGraphState = {
            "question": "测试问题",
            "session_id": "test_session",
            "user_name": "test_user",
        }
        assert state["question"] == "测试问题"
        assert state["session_id"] == "test_session"
        assert state["user_name"] == "test_user"

    @pytest.mark.unit
    def test_type_check(self):
        """测试类型检查"""
        # 测试完整状态
        state: ChartGraphState = {
            "question": "测试问题",
            "session_id": "test_session",
            "user_name": "test_user",
            "sql_result": "SQL结果",
            "code_raw": "原始代码",
            "code": "纯净代码",
            "feedback": "反馈信息",
            "eval_pass": True,
            "attempts": 1,
            "chart_html": "<html></html>",
            "error": "",
        }
        assert isinstance(state["eval_pass"], bool)
        assert isinstance(state["attempts"], int)
        assert isinstance(state["question"], str)


class TestExtractPythonCodeBlock:
    """提取Python代码块函数测试"""

    @pytest.mark.unit
    def test_code_extraction_regex(self):
        """测试代码提取正则"""
        # 测试带markdown标记的代码块
        text = '```python\nprint("hello")\n```'
        result = _extract_python_code_block(text)
        assert result == 'print("hello")'

        # 测试多行代码
        text = '```python\nimport pyecharts\nprint("hello")\n```'
        result = _extract_python_code_block(text)
        assert "import pyecharts" in result
        assert 'print("hello")' in result

    @pytest.mark.unit
    def test_no_markdown_fallback(self):
        """测试无markdown标记时回退到完整文本"""
        # 测试无markdown标记的纯代码
        text = 'print("hello")'
        result = _extract_python_code_block(text)
        assert result == 'print("hello")'

        # 测试无标记的多行代码
        text = 'import pyecharts\nprint("hello")'
        result = _extract_python_code_block(text)
        assert result == text.strip()

    @pytest.mark.unit
    def test_multiple_code_blocks(self):
        """测试多个代码块时只取第一个"""
        # 测试多个代码块
        text = '```python\nprint("first")\n```\n```python\nprint("second")\n```'
        result = _extract_python_code_block(text)
        assert 'print("first")' in result
        assert 'print("second")' not in result


class TestStaticEval:
    """静态代码评估函数测试"""

    @pytest.mark.unit
    def test_static_code_check(self):
        """测试静态代码检查"""
        # 测试缺少CHART_HTML的代码
        code = 'print("hello")'
        passed, issues, feedback = _static_eval(code)
        assert passed is False
        assert len(issues) > 0
        assert "CHART_HTML" in issues[0] or "CHART_HTML_START" in issues[0]

    @pytest.mark.unit
    def test_safety_detection(self):
        """测试安全检测"""
        # 测试包含禁止令牌的代码
        code = '''
import os
CHART_HTML = "test"
print("CHART_HTML_START")
print(CHART_HTML)
print("CHART_HTML_END")
'''
        passed, issues, feedback = _static_eval(code)
        assert passed is False
        assert any("os" in issue for issue in issues)

    @pytest.mark.unit
    def test_from_import_form(self):
        """测试from pyecharts.xxx import yyy形式检测"""
        # 测试合法的from import
        code = '''
from pyecharts.charts import Bar
CHART_HTML = "test"
print("CHART_HTML_START")
print(CHART_HTML)
print("CHART_HTML_END")
'''
        passed, issues, feedback = _static_eval(code)
        # pyecharts是允许的，应该通过
        assert passed is True or not any("pyecharts" in issue for issue in issues)

    @pytest.mark.unit
    def test_banned_tokens_partial_match(self):
        """测试banned_tokens部分匹配误判"""
        # 测试包含"open("的合法代码（如pyecharts中的open）
        # 注意：banned_tokens中有"open("，可能会误判
        code = '''
import pyecharts
CHART_HTML = "test"
print("CHART_HTML_START")
print(CHART_HTML)
print("CHART_HTML_END")
'''
        passed, issues, feedback = _static_eval(code)
        # pyecharts是允许的，不应被误判
        assert "pyecharts" not in str(issues)

    @pytest.mark.unit
    def test_valid_pyecharts_code_pass(self):
        """测试合法pyecharts代码应通过"""
        # 测试完全合法的pyecharts代码
        code = '''
from pyecharts.charts import Bar
from pyecharts import options as opts

bar = Bar()
bar.set_global_opts(title_opts=opts.TitleOpts(title="测试"))
CHART_HTML = bar.render_embed()
print("CHART_HTML_START")
print(CHART_HTML)
print("CHART_HTML_END")
'''
        passed, issues, feedback = _static_eval(code)
        assert passed is True
        assert len(issues) == 0


class TestRouteAfterEval:
    """评估后路由函数测试"""

    @pytest.mark.unit
    def test_route_logic(self):
        """测试条件路由逻辑"""
        # 测试eval_pass=True时前往sandbox
        state: ChartGraphState = {
            "eval_pass": True,
            "attempts": 1,
        }
        result = _route_after_eval(state)
        assert result == "pyecharts_sandbox"

        # 测试eval_pass=False且attempts<3时返回pythonagent
        state = {
            "eval_pass": False,
            "attempts": 1,
        }
        result = _route_after_eval(state)
        assert result == "pythonagent"

    @pytest.mark.unit
    def test_eval_pass_false_max_attempts(self):
        """测试eval_pass=False且attempts>=3时返回END"""
        state: ChartGraphState = {
            "eval_pass": False,
            "attempts": 3,
        }
        result = _route_after_eval(state)
        assert result == END

        # 测试attempts>3
        state = {
            "eval_pass": False,
            "attempts": 4,
        }
        result = _route_after_eval(state)
        assert result == END

    @pytest.mark.unit
    def test_eval_pass_true(self):
        """测试eval_pass=True时前往sandbox"""
        state: ChartGraphState = {
            "eval_pass": True,
            "attempts": 2,
        }
        result = _route_after_eval(state)
        assert result == "pyecharts_sandbox"


class TestRouteAfterSandbox:
    """沙箱后路由函数测试"""

    @pytest.mark.unit
    def test_route_logic(self):
        """测试条件路由逻辑"""
        # 测试有chart_html时返回END
        state: ChartGraphState = {
            "chart_html": "<html></html>",
            "attempts": 1,
        }
        result = _route_after_sandbox(state)
        assert result == END

    @pytest.mark.unit
    def test_has_chart_html(self):
        """测试有chart_html时返回END"""
        state: ChartGraphState = {
            "chart_html": "<html>chart</html>",
            "error": "",
            "attempts": 1,
        }
        result = _route_after_sandbox(state)
        assert result == END

    @pytest.mark.unit
    def test_has_error_max_attempts(self):
        """测试有error且attempts>=3时返回END"""
        state: ChartGraphState = {
            "chart_html": "",
            "error": "执行错误",
            "attempts": 3,
        }
        result = _route_after_sandbox(state)
        assert result == END

    @pytest.mark.unit
    def test_has_error_retry(self):
        """测试有error且attempts<3时返回pythonagent"""
        state: ChartGraphState = {
            "chart_html": "",
            "error": "执行错误",
            "attempts": 1,
        }
        result = _route_after_sandbox(state)
        assert result == "pythonagent"

        state = {
            "chart_html": "",
            "error": "执行错误",
            "attempts": 2,
        }
        result = _route_after_sandbox(state)
        assert result == "pythonagent"

    @pytest.mark.unit
    def test_unknown_state(self):
        """测试既无chart_html又无error的未知状态处理"""
        state: ChartGraphState = {
            "attempts": 1,
        }
        result = _route_after_sandbox(state)
        # 未知状态应该返回END
        assert result == END
