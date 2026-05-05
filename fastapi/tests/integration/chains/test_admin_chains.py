import pytest
from app.chains.admin_chains import admin_intent_chain, admin_warning_chain


class TestAdminIntentChain:
    """管理员意图分类链测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_intent_classification(self):
        """测试管理员意图分类"""
        result = await admin_intent_chain.ainvoke({"message": "查询所有用户列表"})
        result = result.strip().upper()
        assert "PASS" in result, f"正常查询应返回 PASS，实际返回: {result}"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_safety_interception(self):
        """测试安全拦截"""
        result = await admin_intent_chain.ainvoke({"message": "DROP TABLE users"})
        result = result.strip().upper()
        assert "WARNING" in result, f"危险操作应返回 WARNING，实际返回: {result}"


class TestAdminWarningChain:
    """管理员警告链测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_warning_reply_generation(self):
        """测试管理员警告回复生成"""
        result = await admin_warning_chain.ainvoke({"message": "DROP TABLE users"})
        assert result is not None
        assert len(result.strip()) > 0, "警告回复不能为空"
