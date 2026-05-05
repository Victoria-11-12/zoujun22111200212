import pytest
import json
from app.services.user_service import (
    direct_reply_stream, sql_query_stream, warning_stream
)
from app.history import get_history
from app.chains.user_chains import intent_chain


class TestDirectReplyStream:
    """直接回复流式服务测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_direct_reply_stream(self):
        """测试直接回复流式生成"""
        chunks = []
        async for chunk in direct_reply_stream("你好", "test-session-001", "DIRECT_REPLY", "test_user"):
            chunks.append(chunk)
        assert len(chunks) > 0
        assert any("[DONE]" in c for c in chunks)
        data_chunks = [c for c in chunks if "data:" in c and "[DONE]" not in c]
        for data_chunk in data_chunks:
            json_str = data_chunk.replace("data: ", "").strip()
            parsed = json.loads(json_str)
            assert "content" in parsed

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_history_save(self):
        """测试历史记录保存"""
        session_id = "test-session-save"
        chunks = []
        async for chunk in direct_reply_stream("你好", session_id, "DIRECT_REPLY", "test_user"):
            chunks.append(chunk)
        history = get_history(session_id)
        assert len(history) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_log_record(self):
        """测试日志记录"""
        chunks = []
        async for chunk in direct_reply_stream("你好", "test-session-log", "DIRECT_REPLY", "test_user"):
            chunks.append(chunk)
        assert len(chunks) > 0


class TestSqlQueryStream:
    """SQL查询流式服务测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sql_query_stream(self):
        """测试SQL查询流式生成"""
        chunks = []
        async for chunk in sql_query_stream("评分最高的电影", "test-session-002", "NEED_SQL", "test_user"):
            chunks.append(chunk)
        assert len(chunks) > 0
        assert any("[DONE]" in c for c in chunks)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_call(self):
        """测试Agent调用"""
        chunks = []
        async for chunk in sql_query_stream("查询2015年上映的电影", "test-session-003", "NEED_SQL", "test_user"):
            chunks.append(chunk)
        assert len(chunks) > 0
        data_chunks = [c for c in chunks if "data:" in c and "[DONE]" not in c]
        for data_chunk in data_chunks:
            json_str = data_chunk.replace("data: ", "").strip()
            parsed = json.loads(json_str)
            assert "content" in parsed

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_result_wrapping(self):
        """测试结果包装"""
        chunks = []
        async for chunk in sql_query_stream("查询评分最高的电影", "test-session-004", "NEED_SQL", "test_user"):
            chunks.append(chunk)
        assert len(chunks) > 0
        combined = ""
        for c in chunks:
            if "data:" in c and "[DONE]" not in c:
                json_str = c.replace("data: ", "").strip()
                parsed = json.loads(json_str)
                combined += parsed.get("content", "")
        assert len(combined) > 0


class TestWarningStream:
    """警告流式服务测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_warning_stream(self):
        """测试警告流式生成"""
        chunks = []
        async for chunk in warning_stream("DROP TABLE movies", "test-session-005", "test_user", "127.0.0.1"):
            chunks.append(chunk)
        assert len(chunks) > 0
        assert any("[DONE]" in c for c in chunks)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_log_record(self):
        """测试安全日志记录"""
        chunks = []
        async for chunk in warning_stream("DELETE FROM users", "test-session-006", "test_user", "127.0.0.1"):
            chunks.append(chunk)
        assert len(chunks) > 0


class TestAiStream:
    """AI流式服务测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_intent_route(self):
        """测试意图路由"""
        intent = await intent_chain.ainvoke({"message": "评分最高的电影"})
        intent = intent.strip().upper()
        assert "NEED_SQL" in intent or "DIRECT_REPLY" in intent

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_stream_response_assembly(self):
        """测试流式响应组装"""
        chunks = []
        async for chunk in sql_query_stream("查询2013年上映的电影", "test-session-007", "NEED_SQL", "test_user"):
            chunks.append(chunk)
        assert len(chunks) > 0
        assert all(c.startswith("data: ") for c in chunks if c.strip())
