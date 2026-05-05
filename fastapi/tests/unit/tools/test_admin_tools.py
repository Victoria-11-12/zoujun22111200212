import pytest
import re
from app.tools.admin_tools import DANGEROUS_KEYWORDS, check_sql_safety, admin_tools


class TestDangerousKeywords:
    """危险关键词列表测试"""

    @pytest.mark.unit
    def test_list_not_empty(self):
        """测试列表非空"""
        # 验证危险关键词列表不为空
        assert len(DANGEROUS_KEYWORDS) > 0
        # 验证列表包含常见DDL关键词
        assert len(DANGEROUS_KEYWORDS) == 8

    @pytest.mark.unit
    def test_regex_compilable(self):
        """测试正则可编译"""
        # 验证所有关键词都可以编译为正则表达式
        for pattern in DANGEROUS_KEYWORDS:
            compiled = re.compile(pattern)
            assert compiled is not None

    @pytest.mark.unit
    def test_ddl_keywords_coverage(self):
        """测试覆盖DDL关键词"""
        # 验证包含常见DDL关键词
        ddl_keywords = ['DROP', 'TRUNCATE', 'ALTER', 'CREATE']
        patterns_str = ' '.join(DANGEROUS_KEYWORDS)
        for keyword in ddl_keywords:
            assert keyword in patterns_str

    @pytest.mark.unit
    def test_injection_patterns_coverage(self):
        """测试覆盖注入模式"""
        # 验证包含SQL注入模式
        injection_patterns = ['--', ';']
        patterns_str = ' '.join(DANGEROUS_KEYWORDS)
        for pattern in injection_patterns:
            assert pattern in patterns_str


class TestCheckSqlSafety:
    """SQL安全检测函数测试"""

    @pytest.mark.unit
    def test_dangerous_keyword_detection(self):
        """测试危险关键词检测"""
        # 测试DROP关键词
        is_safe, reason = check_sql_safety("DROP TABLE users")
        assert is_safe is False
        assert "DROP" in reason

        # 测试TRUNCATE关键词
        is_safe, reason = check_sql_safety("TRUNCATE TABLE logs")
        assert is_safe is False

        # 测试ALTER关键词
        is_safe, reason = check_sql_safety("ALTER TABLE users ADD COLUMN test")
        assert is_safe is False

    @pytest.mark.unit
    def test_regex_matching(self):
        """测试正则匹配"""
        # 测试GRANT关键词
        is_safe, reason = check_sql_safety("GRANT ALL PRIVILEGES")
        assert is_safe is False
        assert "GRANT" in reason

        # 测试REVOKE关键词
        is_safe, reason = check_sql_safety("REVOKE ALL PRIVILEGES")
        assert is_safe is False

    @pytest.mark.unit
    def test_comment_in_middle_position(self):
        """测试注释符在SQL中间位置检测"""
        # 测试注释符在中间
        is_safe, reason = check_sql_safety("SELECT * FROM users -- comment")
        assert is_safe is False
        assert "--" in reason

    @pytest.mark.unit
    def test_semicolon_followed_by_keyword(self):
        """测试分号后跟关键字匹配"""
        # 测试分号后跟关键字
        is_safe, reason = check_sql_safety("SELECT * FROM users; DROP TABLE users")
        assert is_safe is False

    @pytest.mark.unit
    def test_case_insensitive_bypass(self):
        """测试大小写混合绕过尝试"""
        # 测试大小写混合
        is_safe, reason = check_sql_safety("drop table users")
        assert is_safe is False

        is_safe, reason = check_sql_safety("DrOp TaBlE users")
        assert is_safe is False

        is_safe, reason = check_sql_safety("DROP table USERS")
        assert is_safe is False

    @pytest.mark.unit
    def test_safe_sql_pass(self):
        """测试安全SQL应通过"""
        # 测试安全的SELECT语句
        is_safe, reason = check_sql_safety("SELECT * FROM users WHERE id = 1")
        assert is_safe is True
        assert reason == "通过"

        # 测试安全的UPDATE语句
        is_safe, reason = check_sql_safety("UPDATE users SET name = 'test' WHERE id = 1")
        assert is_safe is True

        # 测试安全的DELETE语句
        is_safe, reason = check_sql_safety("DELETE FROM logs WHERE id = 1")
        assert is_safe is True


class TestAdminTools:
    """管理员工具列表测试"""

    @pytest.mark.unit
    def test_list_completeness(self):
        """测试列表完整性验证(4项工具)"""
        # 验证管理员工具列表包含4项工具
        assert len(admin_tools) == 4

    @pytest.mark.unit
    def test_tool_names_correct(self):
        """测试工具名称正确"""
        # 获取所有工具名称
        tool_names = [tool.name for tool in admin_tools]

        # 验证包含预期的工具名称
        assert "create_user" in tool_names
        assert "safe_execute_sql" in tool_names
        assert "rollback_batch" in tool_names
        assert "start_batch" in tool_names
