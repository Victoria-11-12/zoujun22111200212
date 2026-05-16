# 测试 DeepSeek Flash 模型的 tool_choice 参数支持

import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

# 初始化 LLM（禁用思考模式）
llm = ChatOpenAI(
    model=os.getenv('MODEL_NAME'),
    openai_api_key=os.getenv('API_KEY'),
    openai_api_base=os.getenv('API_BASE'),
    temperature=0.1,
    streaming=False,
    extra_body={"thinking": {"type": "disabled"}},
)

# 定义测试工具
@tool
def rollback_batch() -> str:
    """回滚/撤销数据库操作。当用户说"回滚"、"撤销"、"恢复"时必须调用此工具。"""
    return "回滚成功"

@tool
def query_data(sql: str) -> str:
    """执行SQL查询"""
    return f"查询结果: {sql}"

# 绑定工具
tools = [rollback_batch, query_data]
llm_with_tools = llm.bind_tools(tools)

print("=" * 50)
print("测试1: 普通调用（不指定 tool_choice）")
print("=" * 50)
result1 = llm_with_tools.invoke([HumanMessage(content="帮我回滚刚才的操作")])
print(f"工具调用: {result1.tool_calls}")
print(f"回复内容: {result1.content}")
print()

print("=" * 50)
print("测试2: 强制调用 rollback_batch（tool_choice 指定工具名）")
print("=" * 50)
try:
    result2 = llm_with_tools.invoke(
        [HumanMessage(content="帮我回滚刚才的操作")],
        tool_choice={"type": "function", "function": {"name": "rollback_batch"}}
    )
    print(f"工具调用: {result2.tool_calls}")
    print(f"回复内容: {result2.content}")
except Exception as e:
    print(f"报错: {e}")

print()
print("=" * 50)
print("测试3: tool_choice='auto'")
print("=" * 50)
try:
    result3 = llm_with_tools.invoke(
        [HumanMessage(content="帮我回滚刚才的操作")],
        tool_choice="auto"
    )
    print(f"工具调用: {result3.tool_calls}")
    print(f"回复内容: {result3.content}")
except Exception as e:
    print(f"报错: {e}")

print()
print("=" * 50)
print("测试4: tool_choice='any'（强制调用任意工具）")
print("=" * 50)
try:
    result4 = llm_with_tools.invoke(
        [HumanMessage(content="帮我回滚刚才的操作")],
        tool_choice="any"
    )
    print(f"工具调用: {result4.tool_calls}")
    print(f"回复内容: {result4.content}")
except Exception as e:
    print(f"报错: {e}")
