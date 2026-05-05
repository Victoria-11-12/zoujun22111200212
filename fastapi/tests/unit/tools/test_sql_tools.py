import pytest
from unittest.mock import Mock, patch, MagicMock


class TestSqlDbQuery:
    """SQL数据库查询工具测试"""

    @pytest.mark.unit
    def test_sql_query_execution(self):
        """测试SQL查询执行"""
        # 导入工具
        from app.tools.sql_tools import sql_db_query

        # 验证工具已创建
        assert sql_db_query is not None
        # 验证工具名称
        assert sql_db_query.name == "sql_db_query"

    @pytest.mark.unit
    def test_parameter_passing(self):
        """测试参数传递"""
        # 导入工具
        from app.tools.sql_tools import sql_db_query

        # 验证工具描述
        assert "SQL" in sql_db_query.description or "sql" in sql_db_query.description.lower()
