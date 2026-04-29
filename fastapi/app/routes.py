import json
from fastapi import Request
from fastapi.responses import StreamingResponse

from app.models import ChatRequest
from app.config import llm
from app.history import get_history, save_history, MAX_HISTORY
from app.logs import log_user_chat, log_security_warning
from app.chains import intent_chain, direct_chain, wrap_chain, warning_chain
from app.sql_agent import sql_executor


#六、用户流式生成器
#直接回复流式生成器
async def direct_reply_stream(message: str, session_id: str, intent: str, user_name: str):
    history = get_history(session_id)[-MAX_HISTORY * 2:]
    log_user_chat(session_id, "user", message, intent=intent, user_name=user_name)
    reply = ''
    async for chunk in direct_chain.astream({"message": message, "history": history}):
        reply += chunk
        yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"
    save_history(session_id, message, reply)
    log_user_chat(session_id, "ai", reply, intent=intent, user_name=user_name)


#SQL查询流式生成器
async def sql_query_stream(message: str, session_id: str, intent: str, user_name: str):
    history = get_history(session_id)[-MAX_HISTORY * 2:]
    log_user_chat(session_id, "user", message, intent=intent, user_name=user_name)
    
    result = await sql_executor.ainvoke({"input": message})
    sql_result = result.get('output', '')
    reply = ''
    async for chunk in wrap_chain.astream({"question": message, "result": sql_result, "history": history}):
        reply += chunk
        yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"
    save_history(session_id, message, reply)
    log_user_chat(session_id, "ai", reply, intent=intent, user_name=user_name)


#警告回复流式生成器
async def warning_stream(message: str, session_id: str, user_name: str, client_ip: str):
    reply = ''
    async for chunk in warning_chain.astream({"message": message}):
        reply += chunk
        yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"
    log_security_warning(session_id, user_name, client_ip, "user", message, "意图路由检测")
    log_security_warning(session_id, user_name, client_ip, "ai", reply, "系统警告回复")


# 七、普通用户 AI 接口
async def ai_stream(request: ChatRequest, req: Request):
    """AI 流式对话接口（普通用户）"""
    message = request.message
    session_id = request.sessionId
    client_ip = request.clientIp or (req.client.host if req.client else "")
    user_name = request.username

    async def generate():
        try:
            intent = await intent_chain.ainvoke({"message": message})
            intent = intent.strip().upper()
            print(f"意图判断: {intent}, 问题: {message}")

            if "WARNING" in intent:
                async for chunk in warning_stream(message, session_id, user_name, client_ip):
                    yield chunk
            elif "DIRECT_REPLY" in intent:
                async for chunk in direct_reply_stream(message, session_id, intent, user_name):
                    yield chunk
            else:
                async for chunk in sql_query_stream(message, session_id, intent, user_name):
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
