import pytest
from app.history import conversation_history, MAX_HISTORY, get_history, save_history
from langchain_core.messages import HumanMessage, AIMessage


class TestConversationHistory:
    """对话历史字典测试"""

    @pytest.mark.unit
    def test_global_dict_initialization(self):
        """测试全局字典初始化"""
        # 测试conversation_history是字典类型
        assert isinstance(conversation_history, dict)
        # 测试初始状态可能为空或包含数据
        # 每次测试运行状态可能不同，只验证类型


class TestMaxHistory:
    """最大历史记录常量测试"""

    @pytest.mark.unit
    def test_constant_value(self):
        """测试常量值验证"""
        # 测试MAX_HISTORY值为10
        assert MAX_HISTORY == 10
        # 测试MAX_HISTORY是整数类型
        assert isinstance(MAX_HISTORY, int)


class TestGetHistory:
    """获取历史记录函数测试"""

    @pytest.mark.unit
    def test_existing_session_id(self):
        """测试存在会话ID的处理"""
        # 准备测试数据
        test_session = "test_session_existing"
        test_history = [HumanMessage(content="用户消息"), AIMessage(content="AI消息")]
        conversation_history[test_session] = test_history

        # 执行函数
        result = get_history(test_session)

        # 验证结果
        assert result == test_history
        assert len(result) == 2

        # 清理测试数据
        del conversation_history[test_session]

    @pytest.mark.unit
    def test_non_existing_session_id(self):
        """测试不存在会话ID的处理"""
        # 执行函数，使用不存在的会话ID
        result = get_history("non_existing_session_12345")

        # 验证返回空列表
        assert result == []
        assert isinstance(result, list)


class TestSaveHistory:
    """保存历史记录函数测试"""

    @pytest.mark.unit
    def test_message_append(self):
        """测试消息追加"""
        # 准备测试数据
        test_session = "test_session_append"
        conversation_history[test_session] = []

        # 执行函数
        save_history(test_session, "用户问题", "AI回答")

        # 验证结果
        history = conversation_history[test_session]
        assert len(history) == 2
        assert isinstance(history[0], HumanMessage)
        assert isinstance(history[1], AIMessage)
        assert history[0].content == "用户问题"
        assert history[1].content == "AI回答"

        # 清理测试数据
        del conversation_history[test_session]

    @pytest.mark.unit
    def test_history_truncation(self):
        """测试历史截断"""
        # 准备测试数据，超过MAX_HISTORY*2条记录
        test_session = "test_session_truncation"
        conversation_history[test_session] = []

        # 添加超过限制的记录（MAX_HISTORY=10，所以添加11轮对话=22条消息）
        for i in range(11):
            save_history(test_session, f"用户问题{i}", f"AI回答{i}")

        # 验证历史被截断到MAX_HISTORY*2条
        history = conversation_history[test_session]
        assert len(history) == MAX_HISTORY * 2

        # 验证保留的是最新的记录
        assert "用户问题10" in history[-2].content
        assert "AI回答10" in history[-1].content

        # 清理测试数据
        del conversation_history[test_session]

    @pytest.mark.unit
    def test_langchain_message_wrapper(self):
        """测试LangChain消息封装"""
        # 准备测试数据
        test_session = "test_session_wrapper"
        conversation_history[test_session] = []

        # 执行函数
        save_history(test_session, "测试消息", "测试回复")

        # 验证消息类型
        history = conversation_history[test_session]
        assert isinstance(history[0], HumanMessage)
        assert isinstance(history[1], AIMessage)

        # 清理测试数据
        del conversation_history[test_session]

    @pytest.mark.unit
    def test_exact_max_history_boundary(self):
        """测试恰好等于MAX_HISTORY*2时不截断"""
        # 准备测试数据
        test_session = "test_session_boundary"
        conversation_history[test_session] = []

        # 添加恰好MAX_HISTORY轮对话（20条消息）
        for i in range(MAX_HISTORY):
            save_history(test_session, f"用户问题{i}", f"AI回答{i}")

        # 验证历史长度恰好为MAX_HISTORY*2
        history = conversation_history[test_session]
        assert len(history) == MAX_HISTORY * 2

        # 清理测试数据
        del conversation_history[test_session]

    @pytest.mark.unit
    def test_exceed_max_history(self):
        """测试超过1条时截断至MAX_HISTORY*2"""
        # 准备测试数据
        test_session = "test_session_exceed"
        conversation_history[test_session] = []

        # 添加MAX_HISTORY+1轮对话
        for i in range(MAX_HISTORY + 1):
            save_history(test_session, f"用户问题{i}", f"AI回答{i}")

        # 验证历史被截断
        history = conversation_history[test_session]
        assert len(history) == MAX_HISTORY * 2

        # 清理测试数据
        del conversation_history[test_session]

    @pytest.mark.unit
    def test_empty_string_message(self):
        """测试空字符串消息处理"""
        # 准备测试数据
        test_session = "test_session_empty"
        conversation_history[test_session] = []

        # 执行函数，传入空字符串
        save_history(test_session, "", "")

        # 验证空字符串也能正常保存
        history = conversation_history[test_session]
        assert len(history) == 2
        assert history[0].content == ""
        assert history[1].content == ""

        # 清理测试数据
        del conversation_history[test_session]
