import pytest
import json
from app.services.admin_service import admin_warning_stream
from app.chains.admin_chains import admin_intent_chain


class TestAdminWarningStream:
    """管理员警告流式服务测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_warning_stream(self):
        """测试管理员警告流式生成"""
        chunks = []
        async for chunk in admin_warning_stream("DROP TABLE users", "test-session-admin-001", "admin", "127.0.0.1"):
            chunks.append(chunk)
        assert len(chunks) > 0
        assert any("[DONE]" in c for c in chunks)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_log(self):
        """测试安全日志记录"""
        chunks = []
        async for chunk in admin_warning_stream("DELETE FROM users", "test-session-admin-002", "admin", "127.0.0.1"):
            chunks.append(chunk)
        assert len(chunks) > 0
        data_chunks = [c for c in chunks if "data:" in c and "[DONE]" not in c]
        for data_chunk in data_chunks:
            json_str = data_chunk.replace("data: ", "").strip()
            parsed = json.loads(json_str)
            assert "content" in parsed


class TestAdminAiStream:
    """管理员AI流式服务测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_intent_route(self):
        """测试管理员意图路由"""
        intent = await admin_intent_chain.ainvoke({"message": "查询所有用户"})
        intent = intent.strip().upper()
        assert "PASS" in intent or "WARNING" in intent

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_agent_call(self):
        """测试管理员Agent调用"""
        from app.agents.admin_agent import admin_executor
        from app.tools.admin_tools import set_current_admin_name
        set_current_admin_name("test_admin")
        result = await admin_executor.ainvoke({
            "input": "查询users表",
            "history": []
        })
        assert result is not None
        assert "output" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_stream_response(self):
        """测试流式响应"""
        from app.agents.admin_agent import admin_executor
        from app.tools.admin_tools import set_current_admin_name
        set_current_admin_name("test_admin")
        result = await admin_executor.ainvoke({
            "input": "查询users表前5条记录",
            "history": []
        })
        assert result is not None
        assert len(result.get("output", "")) > 0
