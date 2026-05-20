import os
import sys
import time

if sys.platform == 'win32':
    os.environ['DOCKER_HOST'] = 'npipe:////./pipe/docker_engine'

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from dotenv import load_dotenv
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.metrics import registry, http_requests_total, http_request_duration_seconds
import app.token_tracker  # noqa: F401 — 确保 token 指标注册到 registry
from app.routers import user, admin, chart, analyst

load_dotenv()

app = FastAPI(
    title="电影数据分析系统",
    description="基于 LangChain 和 LangGraph 的智能电影数据查询与可视化系统",
    version="1.0.0"
)

# 请求统计中间件
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    endpoint = request.url.path
    http_requests_total.labels(
        service='fastapi',
        method=request.method,
        endpoint=endpoint,
        status=response.status_code
    ).inc()
    http_request_duration_seconds.labels(
        service='fastapi',
        endpoint=endpoint
    ).observe(duration)
    return response

# Prometheus 指标端点
@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

# 从环境变量读取
# Nginx 代理模式，前端通过 http://localhost 访问
# FRONTEND_URL 环境变量用于生产环境自定义域名
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost')
ALLOWED_ORIGINS = [FRONTEND_URL, "http://localhost"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def cors_preflight_handler(request: Request, call_next):
    origin = request.headers.get("origin")
    if request.method == "OPTIONS" and origin in ALLOWED_ORIGINS:
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response
    response = await call_next(request)
    return response

app.include_router(user.router, prefix="/api", tags=["用户"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理员"])
app.include_router(chart.router, prefix="/api/chart", tags=["图表"])
app.include_router(analyst.router, prefix="/api/analyst", tags=["评估"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
