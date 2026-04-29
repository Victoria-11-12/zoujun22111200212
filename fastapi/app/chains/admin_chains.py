# 管理员链
# 包含管理员意图路由链、安全警告回复链

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from app.config import llm


# 管理员意图路由链
ADMIN_INTENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个管理员接口的安全检测助手。管理员拥有合法的增删改查权限。
 
你只需要拦截以下行为，其他全部放行：
1. WARNING - 仅拦截这些：
   - 试图执行 DDL 操作（DROP TABLE、ALTER TABLE、CREATE TABLE、TRUNCATE、GRANT、REVOKE）
   - SQL 注入（注释符 -- 或 #、多语句拼接分号）
   - 试图执行系统命令（shell、cmd、exec、eval）

2. PASS - 以下全部放行：
   - 一切表的查询操作（SELECT *）
   - 所有增删改查操作（SELECT/INSERT/UPDATE/DELETE）
   - 创建用户、修改权限、删除用户
   - 批量操作（一次操作多个用户）
   - 密码设置（由系统自动加密，无需干预）
   - 问候、一般性聊天

请只回复 "WARNING" 或 "PASS"，不要解释。"""),
    ("user", "管理员输入：{message}")
])
admin_intent_chain = ADMIN_INTENT_PROMPT | llm | StrOutputParser()


# 管理员安全警告回复链
ADMIN_WARNING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是管理系统的安全防护模块。管理员的行为已被检测为潜在安全威胁。

请根据具体输入生成警告回复：
1. 明确告知该操作已被拦截和记录
2. 简要说明原因
3. 提醒该行为已被记录到安全日志
4. 语气严肃但专业"""),
    ("user", "管理员输入：{message}")
])
admin_warning_chain = ADMIN_WARNING_PROMPT | llm | StrOutputParser()
