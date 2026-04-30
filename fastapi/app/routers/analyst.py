# 评估路由
# 定义质量评估相关的API端点

from fastapi import APIRouter

from app.models import EvalQueryRequest, EvaluateRequest
from app.services.analyst_service import start_evaluation, get_progress, query_results


router = APIRouter()


@router.post("/evaluate")
async def api_start_evaluation(request: EvaluateRequest):
    """启动质量评估任务"""
    return await start_evaluation(request)


@router.get("/evaluate/progress")
async def api_get_eval_progress():
    """获取评估进度"""
    return await get_progress()


@router.post("/query")
async def api_query_eval_results(request: EvalQueryRequest):
    """查询评估结果"""
    return await query_results(request)
