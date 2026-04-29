# 图表路由
# 定义图表生成相关的API端点

from fastapi import APIRouter

from app.models import ChartRequest
from app.services.chart_service import chart_generate


router = APIRouter()


@router.post("/generate")
async def api_chart_generate(request: ChartRequest):
    """图表生成接口"""
    return await chart_generate(request)
