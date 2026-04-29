import os

os.environ['DOCKER_HOST'] = 'npipe:////./pipe/docker_engine'

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.models import ChatRequest, ChartRequest, EvalQueryRequest
from app.routers.user import ai_stream
from app.routers.admin import admin_ai_stream
from app.routers.chart import chart_generate
from app.agents.eval_agent import start_evaluation, get_eval_progress, query_eval_results, EvaluateRequest

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#普通用户 AI 接口
@app.post("/api/ai/stream")
async def api_ai_stream(request: ChatRequest, req: Request):
    """AI 流式对话接口（普通用户）"""
    return await ai_stream(request, req)


#管理员 AI 接口
@app.post("/api/admin/ai/stream")
async def api_admin_ai_stream(request: ChatRequest, req: Request):
    """AI 流式对话接口（管理员）"""
    return await admin_ai_stream(request, req)


#图表生成接口
@app.post("/api/chart/generate")
async def api_chart_generate(request: ChartRequest):
    """图表生成接口"""
    return await chart_generate(request)


#评估接口
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
