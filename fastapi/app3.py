import os
import json
import bcrypt
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import tool
import pymysql

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# 一、初始化
# ============================================================

llm = ChatOpenAI(
    model=os.getenv('MODEL_NAME'),
    openai_api_key=os.getenv('API_KEY'),
    openai_api_base=os.getenv('API_BASE'),
    temperature=0.1
)

DB_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
db = SQLDatabase.from_uri(DB_URI)
print(f"数据库连接成功，可用表: {db.get_usable_table_names()}")

# ============================================================
# 二、对话历史管理
# ============================================================

conversation_history: dict[str, list] = {}
MAX_HISTORY = 10


def get_history(session_id: str) -> list:
    return conversation_history.get(session_id, [])


def save_history(session_id: str, user_msg: str, ai_msg: str):
    history = conversation_history.get(session_id, [])
    history.append(HumanMessage(content=user_msg))
    history.append(AIMessage(content=ai_msg))
    if len(history) > MAX_HISTORY * 2:
        history = history[-MAX_HISTORY * 2:]
    conversation_history[session_id] = history


#日志处理
MODEL_NAME = os.getenv('MODEL_NAME', 'unknown')

def log_user_chat(session_id: str, role: str, content: str, intent: str = None, user_name: str = ""):
    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'), database=os.getenv('DB_NAME')
        )
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO user_chat_logs (session_id, user_name, role, content, intent, model_name) VALUES (%s, %s, %s, %s, %s, %s)",
                (session_id, user_name, role, content, intent, MODEL_NAME)
            )
            conn.commit()
    except Exception as e:
        print(f"用户日志记录失败: {e}")
    finally:
        conn.close()


def log_admin_chat(session_id: str, role: str, content: str, user_name: str = ""):
    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'), database=os.getenv('DB_NAME')
        )
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO admin_chat_logs (session_id, user_name, role, content, model_name) VALUES (%s, %s, %s, %s, %s)",
                (session_id, user_name, role, content, MODEL_NAME)
            )
            conn.commit()
    except Exception as e:
        print(f"管理员日志记录失败: {e}")
    finally:
        conn.close()

# ============================================================
# 三、SQL Agent（普通用户查电影数据）
# ============================================================

user_toolkit = SQLDatabaseToolkit(db=db, llm=llm)
sql_agent = create_sql_agent(
    llm=llm,
    toolkit=user_toolkit,
    verbose=True,
    agent_type="tool-calling",
    handle_parsing_errors=True,
    prefix="""你是一个电影数据分析助手。根据用户问题查询数据库，用自然语言回复。
注意：
- 只能执行 SELECT 查询
- 严禁执行 DROP、ALTER、CREATE、DELETE、UPDATE 等操作
- 如果用户的问题与电影数据无关，礼貌地告知你只能回答电影相关的问题"""
)

# ============================================================
# 四、意图判断链
# ============================================================

INTENT_PROMPT = """你是一个意图分类助手。请判断用户的问题是否需要查询电影数据库。

分类规则：
1. NEED_SQL - 需要查询数据库的情况：
   - 询问具体电影信息（如"评分最高的电影"、"2015年上映的电影"）
   - 询问统计数据（如"有多少部电影"、"平均评分"）
   - 询问演员/导演的作品列表
   - 需要具体数据支撑的问题

2. DIRECT_REPLY - 直接回复的情况：
   - 问候语（如"你好"、"早上好"）
   - 关于系统功能的问题（如"你能做什么"）
   - 一般性聊天（如"今天天气怎么样"）
   - 不需要具体数据的问题

请只回复 "NEED_SQL" 或 "DIRECT_REPLY"，不要解释。"""

intent_chain = (
    ChatPromptTemplate.from_messages([
        ("system", INTENT_PROMPT),
        ("human", "用户问题：{message}")
    ])
    | llm
    | StrOutputParser()
)

# ============================================================
# 五、直接回复链（不查数据库）- 加历史记忆
# ============================================================

REPLY_PROMPT = """你是电影数据分析助手。请友好地回复用户。
注意：
- 如果是问候，礼貌回应并介绍自己能查询电影数据
- 如果是无关问题，礼貌告知只能回答电影相关问题
- 回顾之前的对话内容，保持上下文连贯
- 保持友好专业的语气"""

direct_chain = (
    ChatPromptTemplate.from_messages([
        ("system", REPLY_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{message}")
    ])
    | llm
    | StrOutputParser()
)

# ============================================================
# 六、SQL 查询后包装回复链 - 加历史记忆
# ============================================================

wrap_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "你是电影数据分析助手。根据数据库查询结果，用自然语言回答用户问题。注意回顾之前的对话内容，保持上下文连贯。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "用户问题：{question}\n\n查询结果：{result}\n\n请回答：")
    ])
    | llm
    | StrOutputParser()
)

# ============================================================
# 七、流式生成器（异步）- 传入历史
# ============================================================

async def direct_reply_stream(message: str, session_id: str, intent: str = None, user_name: str = ""):
    history = get_history(session_id)
    log_user_chat(session_id, "user", message, intent=intent, user_name=user_name)  # 记用户
    reply = ''
    async for chunk in direct_chain.astream({"message": message, "history": history}):
        reply += chunk
        yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"
    save_history(session_id, message, reply)
    log_user_chat(session_id, "ai", reply, intent=intent, user_name=user_name)  # 记AI


async def sql_query_stream(message: str, session_id: str, intent: str = None, user_name: str = ""):
    history = get_history(session_id)
    log_user_chat(session_id, "user", message, intent=intent, user_name=user_name)
    result = await sql_agent.ainvoke({"input": message})
    sql_result = result.get('output', '')
    reply = ''
    async for chunk in wrap_chain.astream({"question": message, "result": sql_result, "history": history}):
        reply += chunk
        yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"
    save_history(session_id, message, reply)
    log_user_chat(session_id, "ai", reply, intent=intent, user_name=user_name)


# ============================================================
# 八、普通用户 AI 接口
# ============================================================

class ChatRequest(BaseModel):
    message: str
    sessionId: str = ""
    username: str = ""


@app.post("/api/ai/stream")
async def ai_stream(request: ChatRequest):
    """AI 流式对话接口（普通用户）"""
    message = request.message
    session_id = request.sessionId

    async def generate():
        try:
            # 1. 意图判断
            intent = await intent_chain.ainvoke({"message": message})
            intent = intent.strip().upper()
            print(f"意图判断: {intent}, 问题: {message}")

            # 2. 根据意图选择处理方式
            if "DIRECT_REPLY" in intent:
                async for chunk in direct_reply_stream(message, session_id, intent=intent, user_name=request.username):
                    yield chunk
            else:
                async for chunk in sql_query_stream(message, session_id, intent=intent, user_name=request.username):
                    yield chunk

        except Exception as e:
            print(f"AI 普通用户接口报错: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


# ============================================================
# 九、管理员工具（仅保留 create_user）
# ============================================================

@tool
def create_user(username: str, password: str, role: str = "user") -> str:
    """创建新用户，密码会自动加密。参数：username(用户名), password(密码), role(角色,默认user)"""
    conn = pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        database=os.getenv('DB_NAME')
    )
    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return f"用户 {username} 已存在"
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, hashed, role)
            )
            conn.commit()
            return f"用户 {username} 创建成功，角色：{role}"
    finally:
        conn.close()


# ============================================================
# 十、管理员 Agent - 历史记忆 10 轮
# ============================================================

admin_toolkit = SQLDatabaseToolkit(db=db, llm=llm)
admin_tools = [create_user] + admin_toolkit.get_tools()

admin_prompt = ChatPromptTemplate.from_messages([
    ('system', """你是管理员助手，可以查询、删除、修改数据，也可以创建用户。
注意：
- 只能执行 SELECT、DELETE、UPDATE 操作
- 严禁执行 DROP、ALTER、CREATE 等危险操作
- 只能操作以下表：users、logs、user_messages、movies
- 创建用户时密码会自动加密，无需手动处理
- 回复简明直接，不要废话
- 若查询所有信息，需要输出查询到最新十条数据
- 回顾之前的对话内容，保持上下文连贯"""),
    MessagesPlaceholder(variable_name="history"),
    ('user', '{input}'),
    ("placeholder", "{agent_scratchpad}"),
])

admin_agent = create_tool_calling_agent(llm, admin_tools, admin_prompt)
admin_executor = AgentExecutor(agent=admin_agent, tools=admin_tools, verbose=True)


# ============================================================
# 十一、管理员 AI 接口 - 历史记忆 10 轮
# ============================================================

@app.post("/api/admin/ai/stream")
async def admin_ai_stream(request: ChatRequest):
    """AI 流式对话接口（管理员）"""
    message = request.message
    session_id = request.sessionId
    history = get_history(session_id)[-MAX_HISTORY * 2:]  # 保留最近 10 轮

    async def generate():
        try:

            log_admin_chat(session_id, "user", message, user_name=request.username)
            result = await admin_executor.ainvoke({"input": message, "history": history})
            agent_reply = result.get('output', '')

            # 流式输出管理员回复
            for i in range(0, len(agent_reply), 10):
                chunk = agent_reply[i:i + 10]
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            save_history(session_id, message, agent_reply)
            log_admin_chat(session_id, "ai", agent_reply, user_name=request.username)

        except Exception as e:
            print(f"AI 管理员接口报错: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


# ============================================================
# 十二、启动
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
