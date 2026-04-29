# 用户路由
# 定义用户相关的API端点

from fastapi import APIRouter, Request

from app.models import ChatRequest
from app.services.user_service import ai_stream


router = APIRouter()


@router.post("/ai/stream")
async def api_ai_stream(request: ChatRequest, req: Request):
    """AI 流式对话接口（普通用户）"""
    return await ai_stream(request, req)
