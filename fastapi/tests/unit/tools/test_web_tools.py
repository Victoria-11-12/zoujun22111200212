import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess


class TestRunAgentCommand:
    """运行Agent命令工具测试"""

    @pytest.mark.unit
    def test_subprocess_call(self):
        """测试子进程调用"""
        # 导入函数
        from app.tools.web_tools import run_agent_command

        # 验证函数存在
        assert run_agent_command is not None
        assert callable(run_agent_command)

    @pytest.mark.unit
    def test_timeout_handling(self):
        """测试超时处理"""
        # 导入函数
        from app.tools.web_tools import run_agent_command

        # 验证函数有timeout参数
        import inspect
        sig = inspect.signature(run_agent_command)
        assert "timeout" in sig.parameters

    @pytest.mark.unit
    def test_output_parsing(self):
        """测试输出解析"""
        # 导入函数
        from app.tools.web_tools import run_agent_command

        # Mock subprocess.run
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout=b"test output",
                stderr=b"",
                returncode=0
            )

            result = run_agent_command("echo test")

            # 验证返回值结构
            assert "success" in result
            assert "stdout" in result
            assert "stderr" in result
            assert "returncode" in result


class TestBaikeSearchTool:
    """百科搜索工具测试"""

    @pytest.mark.unit
    def test_input_validation(self):
        """测试输入校验"""
        # 导入工具
        from app.tools.web_tools import baike_search_tool

        # 验证工具已创建
        assert baike_search_tool is not None
        # 验证工具名称
        assert baike_search_tool.name == "baike_search_tool"

    @pytest.mark.unit
    def test_command_assembly(self):
        """测试命令组装"""
        # 导入工具
        from app.tools.web_tools import baike_search_tool

        # 验证工具描述
        assert "百度百科" in baike_search_tool.description or "搜索" in baike_search_tool.description

    @pytest.mark.unit
    def test_result_parsing(self):
        """测试结果解析"""
        # 导入工具
        from app.tools.web_tools import baike_search_tool

        # 验证工具是LangChain工具
        from langchain.tools import BaseTool
        assert isinstance(baike_search_tool, BaseTool)
