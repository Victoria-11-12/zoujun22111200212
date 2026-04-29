# 评估服务
# 处理质量评估业务逻辑

from app.models import EvalQueryRequest
from app.agents.eval_agent import (
    start_evaluation,
    get_eval_progress,
    query_eval_results,
    EvaluateRequest
)


# 启动评估任务
async def evaluate(request: EvaluateRequest):
    """启动质量评估任务"""
    return await start_evaluation(request)


# 获取评估进度
async def get_progress():
    """获取评估进度"""
    return await get_eval_progress()


# 查询评估结果
async def query_results(request: EvalQueryRequest):
    """查询评估结果"""
    return await query_eval_results(request)
