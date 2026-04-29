# 管理员服务
# 处理管理员的AI对话业务逻辑

import json
from fastapi import Request
from fastapi.responses import StreamingResponse

from app.models import AdminChatRequest
from app.history import get_history, save_history, MAX_HISTORY
from app.logs import log_admin_chat, log_security_warning
from app.chains.admin_chains import admin_intent_chain, admin_warning_chain
from app.agents.admin_agent import admin_executor
from app.tools.admin_tools import set_current_admin_name


# 管理员的安全警告流式回复
async def admin_warning_stream(message: str, session_id: str, user_name: str = "", client_ip: str = ""):
    reply = ''
    async for chunk in admin_warning_chain.astream({"message": message}):
        reply += chunk
        yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"
    log_security_warning(session_id, user_name, client_ip, "admin", message, "管理员意图路由检测")
    log_security_warning(session_id, user_name, client_ip, "ai", reply, "管理员警告回复")


# 管理员AI流式接口
async def admin_ai_stream(request: AdminChatRequest, req: Request):
    """AI 流式对话接口（管理员）"""
    set_current_admin_name(request.username)
    
    message = request.message
    session_id = request.sessionId
    client_ip = getattr(request, 'clientIp', '') or (req.client.host if req.client else "")
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

            log_admin_chat(session_id, "user", message, user_name=request.username)
            result = await admin_executor.ainvoke({"input": message, "history": history})
            agent_reply = result.get('output', '')

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
