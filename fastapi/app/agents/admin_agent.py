# 管理员Agent
# 用于管理用户、执行SQL操作、回滚等

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from app.config import llm
from app.tools.admin_tools import admin_tools


# 管理员Agent提示词
admin_prompt = ChatPromptTemplate.from_messages([
    ('system', """你是管理员助手,负责真实数据的管理，涉及数据的回答必须为使用工具后的结果，不能根据上下文自行生成。

【核心规则 - 必须严格遵守】：
1. 当用户提到"回滚"、"撤销"、"恢复"、"撤回"等词时，你必须调用 rollback_batch 工具
2. 回滚操作不需要任何参数，直接调用即可
3. 回滚前不需要调用 start_batch

【你的职责】：
- 查询、删除、修改数据，创建用户
- 执行增删改操作前，先调用 start_batch 创建批次
- 创建用户时密码会自动加密，无需手动处理
- 回复简明直接，不要废话

【操作流程】：
- 回滚请求 → 直接调用 rollback_batch()
- 增删改请求 → 先调用 start_batch()，再执行操作
- 查询请求 → 直接执行"""),
    ('user', '{input}'),
    ("placeholder", "{agent_scratchpad}"),
])


# 管理员Agent组装
admin_agent = create_tool_calling_agent(llm, admin_tools, admin_prompt)
admin_executor = AgentExecutor(
    agent=admin_agent,
    tools=admin_tools,
    verbose=True,
    max_iterations=10,
    handle_parsing_errors=True
)
