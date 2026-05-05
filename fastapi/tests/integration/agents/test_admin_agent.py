import pytest
from app.agents.admin_agent import admin_agent, admin_executor, admin_prompt, admin_tools
from app.tools.admin_tools import set_current_admin_name, start_batch, rollback_batch


class TestAdminAgent:
    """管理员Agent测试"""

    @pytest.mark.integration
    def test_agent_initialization(self):
        """测试Agent初始化"""
        assert admin_agent is not None
        assert admin_executor is not None

    @pytest.mark.integration
    def test_prompt_config(self):
        """测试提示词配置"""
        assert admin_prompt is not None
        assert len(admin_tools) == 4
        tool_names = [t.name for t in admin_tools]
        assert "create_user" in tool_names
        assert "safe_execute_sql" in tool_names
        assert "start_batch" in tool_names
        assert "rollback_batch" in tool_names


class TestAdminExecutor:
    """管理员执行器测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_call_chain(self):
        """测试工具调用链"""
        set_current_admin_name("test_admin")
        result = await admin_executor.ainvoke({
            "input": "查询users表所有用户",
            "history": []
        })
        assert result is not None
        assert "output" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_operations(self):
        """测试批量操作"""
        set_current_admin_name("test_admin")
        start_batch.invoke({})
        result = await admin_executor.ainvoke({
            "input": "创建用户 test_integration_user，密码 test123",
            "history": []
        })
        assert result is not None
        assert "output" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rollback_trigger(self):
        """测试回滚触发"""
        set_current_admin_name("test_admin")
        start_batch.invoke({})
        await admin_executor.ainvoke({
            "input": "创建用户 test_rollback_user，密码 test123",
            "history": []
        })
        result = await admin_executor.ainvoke({
            "input": "回滚刚才的操作",
            "history": []
        })
        assert result is not None
        assert "output" in result
