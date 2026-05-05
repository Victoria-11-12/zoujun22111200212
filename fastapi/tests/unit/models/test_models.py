import pytest
from pydantic import ValidationError
from app.models import (
    ChatRequest,
    AdminChatRequest,
    ChartRequest,
    EvaluateRequest,
    EvalQueryRequest,
    ResponseEvalResult,
    CodeEvalResult,
)


class TestChatRequest:
    """聊天请求模型测试"""

    @pytest.mark.unit
    def test_field_validation(self):
        """测试字段验证功能"""
        # 测试有效数据
        request = ChatRequest(
            message="你好",
            sessionId="session123",
            username="testuser",
            clientIp="127.0.0.1",
        )
        assert request.message == "你好"
        assert request.sessionId == "session123"
        assert request.username == "testuser"
        assert request.clientIp == "127.0.0.1"

    @pytest.mark.unit
    def test_default_values(self):
        """测试默认值设置"""
        request = ChatRequest(message="测试消息")
        assert request.message == "测试消息"
        assert request.sessionId == ""
        assert request.username == ""
        assert request.clientIp == ""

    @pytest.mark.unit
    def test_required_fields(self):
        """测试必填字段校验"""
        # 缺少必填字段message时应抛出验证错误
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest()
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("message",) for error in errors)


class TestAdminChatRequest:
    """管理员聊天请求模型测试"""

    @pytest.mark.unit
    def test_field_validation(self):
        """测试字段验证功能"""
        request = AdminChatRequest(
            message="管理员消息",
            sessionId="admin_session",
            username="admin",
            clientIp="192.168.1.1",
        )
        assert request.message == "管理员消息"
        assert request.sessionId == "admin_session"
        assert request.username == "admin"
        assert request.clientIp == "192.168.1.1"

    @pytest.mark.unit
    def test_default_values(self):
        """测试默认值设置"""
        request = AdminChatRequest(message="管理员测试")
        assert request.message == "管理员测试"
        assert request.sessionId == ""
        assert request.username == ""
        assert request.clientIp == ""

    @pytest.mark.unit
    def test_required_fields(self):
        """测试必填字段校验"""
        with pytest.raises(ValidationError) as exc_info:
            AdminChatRequest()
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("message",) for error in errors)


class TestChartRequest:
    """图表生成请求模型测试"""

    @pytest.mark.unit
    def test_field_validation(self):
        """测试字段验证功能"""
        request = ChartRequest(
            message="生成柱状图",
            sessionId="chart_session",
            username="chartuser",
        )
        assert request.message == "生成柱状图"
        assert request.sessionId == "chart_session"
        assert request.username == "chartuser"

    @pytest.mark.unit
    def test_default_values(self):
        """测试默认值设置"""
        request = ChartRequest(message="生成图表")
        assert request.message == "生成图表"
        assert request.sessionId == ""
        assert request.username == ""

    @pytest.mark.unit
    def test_required_fields(self):
        """测试必填字段校验"""
        with pytest.raises(ValidationError) as exc_info:
            ChartRequest()
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("message",) for error in errors)


class TestEvaluateRequest:
    """评估请求模型测试"""

    @pytest.mark.unit
    def test_field_validation(self):
        """测试字段验证功能"""
        request = EvaluateRequest(
            tables=["user_chat_logs", "admin_chat_logs"],
            start_date="2024-01-01",
            end_date="2024-12-31",
        )
        assert request.tables == ["user_chat_logs", "admin_chat_logs"]
        assert request.start_date == "2024-01-01"
        assert request.end_date == "2024-12-31"

    @pytest.mark.unit
    def test_default_values(self):
        """测试默认值设置"""
        request = EvaluateRequest()
        assert request.tables == [
            "user_chat_logs",
            "admin_chat_logs",
            "chart_generation_logs",
            "security_warning_logs",
        ]
        assert request.start_date == ""
        assert request.end_date == ""


class TestEvalQueryRequest:
    """评估查询请求模型测试"""

    @pytest.mark.unit
    def test_field_validation(self):
        """测试字段验证功能"""
        request = EvalQueryRequest(
            table="user_chat_logs",
            start_time="2024-01-01",
            end_time="2024-12-31",
        )
        assert request.table == "user_chat_logs"
        assert request.start_time == "2024-01-01"
        assert request.end_time == "2024-12-31"

    @pytest.mark.unit
    def test_optional_fields(self):
        """测试可选字段处理"""
        # 只提供必填字段
        request = EvalQueryRequest(table="admin_chat_logs")
        assert request.table == "admin_chat_logs"
        assert request.start_time is None
        assert request.end_time is None

        # 提供部分可选字段
        request = EvalQueryRequest(table="chart_generation_logs", start_time="2024-01-01")
        assert request.table == "chart_generation_logs"
        assert request.start_time == "2024-01-01"
        assert request.end_time is None


class TestResponseEvalResult:
    """对话评估结果模型测试"""

    @pytest.mark.unit
    def test_score_range_validation(self):
        """测试分数范围验证(1-5分)"""
        # 测试有效分数
        result = ResponseEvalResult(
            score=3,
            dimensions={"相关性": 5, "完整性": 4, "准确性": 3, "格式": 5},
            issues="无明显问题",
            verdict="pass",
        )
        assert result.score == 3

        # 测试边界值1
        result = ResponseEvalResult(
            score=1,
            dimensions={"相关性": 1},
            issues="问题严重",
            verdict="fail",
        )
        assert result.score == 1

        # 测试边界值5
        result = ResponseEvalResult(
            score=5,
            dimensions={"相关性": 5},
            issues="完美",
            verdict="pass",
        )
        assert result.score == 5

    @pytest.mark.unit
    def test_type_check(self):
        """测试类型检查"""
        # 测试字段类型正确
        result = ResponseEvalResult(
            score=4,
            dimensions={"相关性": 5, "完整性": 4},
            issues="格式需要改进",
            verdict="review",
        )
        assert isinstance(result.score, int)
        assert isinstance(result.dimensions, dict)
        assert isinstance(result.issues, str)
        assert isinstance(result.verdict, str)

        # 测试缺少必填字段
        with pytest.raises(ValidationError) as exc_info:
            ResponseEvalResult()
        errors = exc_info.value.errors()
        field_names = [error["loc"][0] for error in errors]
        assert "score" in field_names
        assert "dimensions" in field_names
        assert "issues" in field_names
        assert "verdict" in field_names


class TestCodeEvalResult:
    """代码评估结果模型测试"""

    @pytest.mark.unit
    def test_score_range_validation(self):
        """测试分数范围验证(1-5分)"""
        # 测试有效分数
        result = CodeEvalResult(
            score=4,
            dimensions={"可运行性": 5, "图表完整性": 4, "工具箱": 3, "单位标注": 5, "类型匹配": 4},
            issues="代码结构良好",
            verdict="pass",
        )
        assert result.score == 4

        # 测试边界值1
        result = CodeEvalResult(
            score=1,
            dimensions={"可运行性": 1},
            issues="代码无法运行",
            verdict="fail",
        )
        assert result.score == 1

        # 测试边界值5
        result = CodeEvalResult(
            score=5,
            dimensions={"可运行性": 5, "图表完整性": 5},
            issues="完美代码",
            verdict="pass",
        )
        assert result.score == 5

    @pytest.mark.unit
    def test_type_check(self):
        """测试类型检查"""
        # 测试字段类型正确
        result = CodeEvalResult(
            score=3,
            dimensions={"可运行性": 3, "图表完整性": 3},
            issues="需要优化",
            verdict="review",
        )
        assert isinstance(result.score, int)
        assert isinstance(result.dimensions, dict)
        assert isinstance(result.issues, str)
        assert isinstance(result.verdict, str)

        # 测试缺少必填字段
        with pytest.raises(ValidationError) as exc_info:
            CodeEvalResult()
        errors = exc_info.value.errors()
        field_names = [error["loc"][0] for error in errors]
        assert "score" in field_names
        assert "dimensions" in field_names
        assert "issues" in field_names
        assert "verdict" in field_names
