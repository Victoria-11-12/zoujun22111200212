# 管理员路由
# 定义管理员相关的API端点

from fastapi import APIRouter, Request

from app.models import AdminChatRequest
from app.services.admin_service import admin_ai_stream


router = APIRouter()


@router.post("/ai/stream")
async def api_admin_ai_stream(request: AdminChatRequest, req: Request):
    """AI 流式对话接口（管理员）"""
    return await admin_ai_stream(request, req)
