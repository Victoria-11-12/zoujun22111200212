import os
import json
import bcrypt
import joblib
import pandas as pd
import numpy as np
import requests
import time
import asyncio
# from dotenv import load_dotenv
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
# from sklearn.preprocessing import LabelEncoder
# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.messages import HumanMessage, AIMessage
# from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
# from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableBranch, RunnableLambda
# from langchain_community.utilities import SQLDatabase
# from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
# from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
# from langchain.tools import tool
# import pymysql

# load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ============================================================
# 一、原有机器学习模块（保持不变）
# ============================================================

try:
    lgb_model = joblib.load('lightgbm_model_1.pkl')
    rf_model = joblib.load('random_forest_model.pkl')
    print("模型加载成功！")
except Exception as e:
    print(f"模型加载失败，请检查文件路径: {e}")

NODE_API_URL = "http://127.0.0.1:3000/api"

label_encoders = {}

dark_horses_cache = {
    'data': None,
    'timestamp': 0,
    'expire_seconds': 300
}

def prepare_features(df):
    df = df.copy()
    if 'genres' not in df.columns:
        df['genres'] = 'unknown'
    else:
        df['genres'] = df['genres'].fillna('unknown')
    if 'director_facebook_likes' in df.columns:
        df['New_Director'] = df['director_facebook_likes'].apply(
            lambda x: 'No' if pd.isna(x) or float(x) == 0 else 'Yes'
        )
    else:
        df['New_Director'] = 'No'
    if 'actor_1_facebook_likes' in df.columns:
        df['New_Actor'] = df['actor_1_facebook_likes'].apply(
            lambda x: 'No' if pd.isna(x) or float(x) == 0 else 'Yes'
        )
    else:
        df['New_Actor'] = 'No'
    if 'budget' in df.columns:
        df['budget'] = pd.to_numeric(df['budget'], errors='coerce').fillna(1000)
    else:
        df['budget'] = 1000
    return df[['genres', 'New_Director', 'New_Actor', 'budget']]


@app.route('/api/flask/dark_horses', methods=['GET'])
def get_dark_horses():
    try:
        current_time = time.time()
        if (dark_horses_cache['data'] is not None and
            current_time - dark_horses_cache['timestamp'] < dark_horses_cache['expire_seconds']):
            return jsonify({"code": 200, "data": dark_horses_cache['data']})

        response = requests.get(f"{NODE_API_URL}/movies")
        movies = response.json()
        df = pd.DataFrame(movies)

        if df.empty:
            return jsonify({"code": 200, "data": []})

        if 'budget' in df.columns:
            df['budget'] = pd.to_numeric(df['budget'], errors='coerce')
            df = df.dropna(subset=['budget'])
            df = df[df['budget'] > 0]
        else:
            return jsonify({"code": 200, "data": []})

        if df.empty:
            return jsonify({"code": 200, "data": []})

        df_features = prepare_features(df.copy())

        cat_cols = ['genres', 'New_Director', 'New_Actor']
        for col in cat_cols:
            if col in df_features.columns:
                if col in ['New_Director', 'New_Actor']:
                    df_features[col] = df_features[col].apply(lambda x: 1 if str(x).strip().lower() == 'yes' else 0)
                else:
                    df_features[col] = df_features[col].apply(lambda x: hash(str(x)) % 2)

        X = df_features[['genres', 'New_Director', 'New_Actor', 'budget']]
        predictions = lgb_model.predict(X)

        df['predicted_gross'] = predictions
        df['predicted_roi'] = df['predicted_gross'] / df['budget']

        dark_horses = df.sort_values('predicted_roi', ascending=False).head(30)
        result = dark_horses[['movie_title', 'budget', 'predicted_gross', 'predicted_roi', 'genres']].to_dict('records')

        dark_horses_cache['data'] = result
        dark_horses_cache['timestamp'] = current_time

        return jsonify({"code": 200, "data": result})
    except Exception as e:
        print(f"黑马筛选报错：{e}")
        import traceback
        traceback.print_exc()
        return jsonify({"code": 500, "msg": str(e)})


@app.route('/api/flask/predict_deep', methods=['POST'])
def predict_deep():
    try:
        data = request.json
        print("接收到的数据:", data)

        features = [
            float(data.get('budget', 0)),
            float(data.get('director_likes', 0)),
            float(data.get('actor1_likes', 0)),
            float(data.get('actor2_likes', 0)),
            float(data.get('actor3_likes', 0)),
            float(data.get('movie_likes', 0)),
            float(data.get('voted_users', 0)),
            float(data.get('review_count', 0)),
            float(data.get('imdb_score', 0))
        ]
        print("构造的特征列表:", features)

        input_data = np.array([features])
        predicted_log = rf_model.predict(input_data)[0]
        predicted = np.expm1(predicted_log)
        print("模型预测的对数值:", predicted_log)
        print("转换后的票房预测:", predicted)

        return jsonify({"code": 200, "predicted_gross": float(predicted)})
    except Exception as e:
        print("预测接口异常:", str(e))
        return jsonify({"code": 500, "msg": str(e)})

# # ============================================================
# # AI 模块 - 普通用户部分
# # ============================================================

# # --- 初始化 LLM ---
# llm = ChatOpenAI(
#     model=os.getenv('MODEL_NAME'),
#     openai_api_key=os.getenv('API_KEY'),
#     openai_api_base=os.getenv('API_BASE'),
#     temperature=0.1
# )

# # --- 连接数据库 ---
# DB_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
# db = SQLDatabase.from_uri(DB_URI)
# print(f"数据库连接成功，可用表: {db.get_usable_table_names()}")

# # --- 对话历史管理 ---
# conversation_history = {}
# MAX_HISTORY = 10


# def get_history(session_id):
#     return conversation_history.get(session_id, [])


# def save_history(session_id, user_msg, ai_msg):
#     history = conversation_history.get(session_id, [])
#     history.append(HumanMessage(content=user_msg))
#     history.append(AIMessage(content=ai_msg))
#     if len(history) > MAX_HISTORY * 2:
#         history = history[-MAX_HISTORY * 2:]
#     conversation_history[session_id] = history


# # --- SQL Agent ---
# user_toolkit = SQLDatabaseToolkit(db=db, llm=llm)
# sql_agent = create_sql_agent(
#     llm=llm,
#     toolkit=user_toolkit,
#     verbose=True,
#     agent_type="tool-calling",
#     handle_parsing_errors=True,
#     prefix="""你是一个电影数据分析助手。根据用户问题查询数据库，用自然语言回复。
# 注意：
# - 只能执行 SELECT 查询
# - 严禁执行 DROP、ALTER、CREATE、DELETE、UPDATE 等操作
# - 如果用户的问题与电影数据无关，礼貌地告知你只能回答电影相关的问题"""
# )

# # --- 意图判断 ---
# INTENT_PROMPT = """你是一个意图分类助手。请判断用户的问题是否需要查询电影数据库。

# 分类规则：
# 1. NEED_SQL - 需要查询数据库的情况：
#    - 询问具体电影信息（如"评分最高的电影"、"2015年上映的电影"）
#    - 询问统计数据（如"有多少部电影"、"平均评分"）
#    - 询问演员/导演的作品列表
#    - 需要具体数据支撑的问题

# 2. DIRECT_REPLY - 直接回复的情况：
#    - 问候语（如"你好"、"早上好"）
#    - 关于系统功能的问题（如"你能做什么"）
#    - 一般性聊天（如"今天天气怎么样"）
#    - 不需要具体数据的问题

# 请只回复 "NEED_SQL" 或 "DIRECT_REPLY"，不要解释。"""

# intent_chain = ChatPromptTemplate.from_messages([
#     ("system", INTENT_PROMPT),
#     ("human", "用户问题：{message}")
# ]) | llm | StrOutputParser()

# # --- 直接回复（不查数据库） ---
# REPLY_PROMPT = """你是电影数据分析助手。请友好地回复用户。
# 注意：
# - 如果是问候，礼貌回应并介绍自己能查询电影数据
# - 如果是无关问题，礼貌告知只能回答电影相关问题
# - 保持友好专业的语气"""

# direct_chain = ChatPromptTemplate.from_messages([
#     ("system", REPLY_PROMPT),
#     ("human", "{message}")
# ]) | llm | StrOutputParser()

# # --- SQL 查询后包装回复 ---
# wrap_chain = ChatPromptTemplate.from_messages([
#     ("system", "你是电影数据分析助手。根据数据库查询结果，用自然语言回答用户问题。"),
#     ("human", "用户问题：{question}\n\n查询结果：{result}\n\n请回答：")
# ]) | llm | StrOutputParser()

# # --- SSE 流式生成器 ---
# def direct_reply_stream(message, session_id):
#     """不查数据库，直接回复，流式输出"""
#     reply = ''
#     for chunk in direct_chain.stream({"message": message}):
#         reply += chunk
#         yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
#     yield "data: [DONE]\n\n"
#     save_history(session_id, message, reply)


# def sql_query_stream(message, session_id):
#     """查数据库，拿到结果后流式输出"""
#     result = sql_agent.invoke({"input": message})
#     sql_result = result.get('output', '')

#     reply = ''
#     for chunk in wrap_chain.stream({"question": message, "result": sql_result}):
#         reply += chunk
#         yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
#     yield "data: [DONE]\n\n"
#     save_history(session_id, message, reply)


# # --- 路由接口 ---
# @app.route('/api/ai/stream', methods=['POST'])
# def ai_stream():
#     """AI流式对话接口（普通用户）"""
#     data = request.json
#     message = data.get('message', '')
#     session_id = data.get('sessionId', '')

#     def generate():
#         try:
#             # 1. 意图判断
#             intent = intent_chain.invoke({"message": message}).strip().upper()
#             print(f"意图判断: {intent}, 问题: {message}")

#             # 2. 根据意图选择处理方式
#             if "DIRECT_REPLY" in intent:
#                 yield from direct_reply_stream(message, session_id)
#             else:
#                 yield from sql_query_stream(message, session_id)

#         except Exception as e:
#             print(f"AI 接口报错: {e}")
#             yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
#             yield "data: [DONE]\n\n"

#     return Response(
#         generate(),
#         mimetype='text/event-stream',
#         headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
#     )

# # --- 2.5 管理员工具（仅保留 create_user） ---
# @tool
# def create_user(username: str, password: str, role: str = "user") -> str:
#     """创建新用户，密码会自动加密。参数：username(用户名), password(密码), role(角色,默认user)"""
#     conn = pymysql.connect(
#         host=os.getenv('DB_HOST'),
#         user=os.getenv('DB_USER'),
#         password=os.getenv('DB_PASS'),
#         database=os.getenv('DB_NAME')
#     )
#     try:
#         hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
#         with conn.cursor() as cursor:
#             cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
#             if cursor.fetchone():
#                 return f"用户 {username} 已存在"
#             cursor.execute(
#                 "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
#                 (username, hashed, role)
#             )
#             conn.commit()
#             return f"用户 {username} 创建成功，角色：{role}"
#     finally:
#         conn.close()


# # --- 2.6 管理员 Agent ---
# admin_toolkit = SQLDatabaseToolkit(db=db, llm=llm)
# admin_tools = [create_user] + admin_toolkit.get_tools()

# admin_prompt = ChatPromptTemplate.from_messages([
#     ('system', """你是管理员助手，可以查询、删除、修改数据，也可以创建用户。
# 注意：
# - 只能执行 SELECT、DELETE、UPDATE 操作
# - 严禁执行 DROP、ALTER、CREATE 等危险操作
# - 只能操作以下表：users、logs、user_messages、movies
# - 创建用户时密码会自动加密，无需手动处理
# - 回复简明直接，不要废话
# - 若查询所有信息，需要输出所有查询的到详细数据"""),
#     MessagesPlaceholder(variable_name="history"),
#     ('user', '{input}'),
#     ("placeholder", "{agent_scratchpad}"),
# ])

# admin_agent = create_tool_calling_agent(llm, admin_tools, admin_prompt)
# admin_executor = AgentExecutor(agent=admin_agent, tools=admin_tools, verbose=True)


# @app.route('/api/admin/ai/stream', methods=['POST'])
# def admin_ai_stream():
#     data = request.json
#     message = data.get('message', '')
#     history = conversation_history[-4:]  # 只保留最近 2 轮

#     async def async_generate():
#         """异步生成器，直接使用Agent结果分段发送"""
#         try:
#             result = admin_executor.invoke({"input": message, "history": history})
#             agent_reply = result.get('output', '')

#             # for i in range(0, len(agent_reply), CHUNK_SIZE):
#             #     chunk = agent_reply[i:i+CHUNK_SIZE]
#             #     yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
#             #     await asyncio.sleep(CHUNK_DELAY)

#             yield "data: [DONE]\n\n"
#             save_history(message, agent_reply)
#         except Exception as e:
#             print(f"AI 管理员接口报错: {e}")
#             import traceback
#             traceback.print_exc()
#             yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
#             yield "data: [DONE]\n\n"

#     def generate():
#         """将异步生成器转换为同步生成器"""
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         async_gen = async_generate()
#         try:
#             while True:
#                 try:
#                     chunk = loop.run_until_complete(async_gen.__anext__())
#                     yield chunk
#                 except StopAsyncIteration:
#                     break
#         finally:
#             loop.close()

#     return Response(
#         generate(),
#         mimetype='text/event-stream',
#         headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
#     )


# # ============================================================
# # 三、启动
# # ============================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
