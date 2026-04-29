import os

os.environ['DOCKER_HOST'] = 'npipe:////./pipe/docker_engine'

import json
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.models import ChatRequest, ChartRequest, EvalQueryRequest
from app.routes import ai_stream
from app.admin import admin_executor, admin_intent_chain, admin_warning_stream
from app.chart_graph import chart_graph
from app.chains import chart_intent_chain, chart_not_chain
from app.eval_module import start_evaluation, get_eval_progress, query_eval_results, EvaluateRequest

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 十一、管理员 AI 路由

@app.post("/api/admin/ai/stream")
async def admin_ai_stream(request: ChatRequest, req: Request):
    """AI 流式对话接口（管理员）"""
    import app.admin as admin_module
    admin_module._current_admin_name = request.username
    
    message = request.message
    session_id = request.sessionId
    client_ip = request.clientIp 
    from app.history import get_history, MAX_HISTORY
    history = get_history(session_id)[-MAX_HISTORY * 2:]

    async def generate():
        try:
            intent = await admin_intent_chain.ainvoke({"message": message})
            intent = intent.strip().upper()
            print(f"[管理员] 意图判断: {intent}, 问题: {message}")

            if "WARNING" in intent:
                async for chunk in admin_warning_stream(message, session_id, user_name=request.username, client_ip=client_ip):
                    yield chunk
                return

            from app.logs import log_admin_chat
            log_admin_chat(session_id, "user", message, user_name=request.username)
            result = await admin_executor.ainvoke({"input": message, "history": history})
            agent_reply = result.get('output', '')

            for i in range(0, len(agent_reply), 10):
                chunk = agent_reply[i:i + 10]
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            from app.history import save_history
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


# 七、普通用户 AI 接口

@app.post("/api/ai/stream")
async def api_ai_stream(request: ChatRequest, req: Request):
    """AI 流式对话接口（普通用户）"""
    return await ai_stream(request, req)


# 图表生成接口

@app.post("/api/chart/generate")
async def chart_generate(request: ChartRequest):

    chart_message = request.message
    session_id = request.sessionId
    user_name = request.username

    intent = await chart_intent_chain.ainvoke({"question": chart_message})
    intent = intent.strip().upper()
    print(f"绘图意图判断: {intent}, 问题: {chart_message}")

    async def generate():
        try:
            if "NOT_CHART" in intent:
                reply = await chart_not_chain.ainvoke({"question": chart_message})
                yield f"data: {json.dumps({'type': 'text', 'content': reply}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                return

            result = await chart_graph.ainvoke(
                {
                    "question": chart_message,
                    "session_id": session_id,
                    "user_name": user_name,
                    "feedback": "",
                    "attempts": 0,
                }
            )

            if result.get("chart_html"):
                yield f"data: {json.dumps({'type': 'chart', 'chart_html': result['chart_html']}, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'text', 'content': result.get('error', '图表生成失败')}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            print(f"绘图接口报错: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'text', 'content': str(e)}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


# 评估接口

@app.post("/api/analyst/evaluate")
async def api_start_evaluation(request: EvaluateRequest):
    """启动质量评估任务"""
    return await start_evaluation(request)


@app.get("/api/analyst/evaluate/progress")
async def api_get_eval_progress():
    """获取评估进度"""
    return await get_eval_progress()


@app.post("/api/analyst/query")
async def api_query_eval_results(request: EvalQueryRequest):
    """查询评估结果"""
    return await query_eval_results(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
