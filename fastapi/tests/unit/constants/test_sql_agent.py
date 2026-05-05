import pytest
from app.agents.sql_agent import user_toolkit


class TestUserToolkit:
    """用户工具包常量测试"""

    @pytest.mark.unit
    def test_list_completeness(self):
        """测试列表完整性验证(2项工具)"""
        # 验证用户工具包列表包含2项工具
        assert len(user_toolkit) == 2

    @pytest.mark.unit
    def test_tool_names_correct(self):
        """测试工具名称正确"""
        # 获取所有工具名称
        tool_names = [tool.name for tool in user_toolkit]

        # 验证包含预期的工具名称
        assert "sql_db_query" in tool_names
        assert "baike_search_tool" in tool_names
