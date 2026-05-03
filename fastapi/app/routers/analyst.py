# 评估路由
# 定义质量评估相关的API端点

from fastapi import APIRouter

from app.models import EvalQueryRequest, EvaluateRequest
from app.services.analyst_service import start_evaluation, get_progress, query_results, get_results_stats


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


@router.get("/results")
async def api_get_results_stats(
    min_score: int = 0,
    source_table: str = "",
    tables: str = "",
    start_date: str = "",
    end_date: str = ""
):
    """获取评估结果统计，用于前端画图展示"""
    return await get_results_stats(min_score, source_table, tables, start_date, end_date)
