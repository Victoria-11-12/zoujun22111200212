import os

os.environ['DOCKER_HOST'] = 'npipe:////./pipe/docker_engine'

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from dotenv import load_dotenv

from app.routers import user, admin, chart, analyst

load_dotenv()

app = FastAPI(
    title="电影数据分析系统",
    description="基于LangChain和LangGraph的智能电影数据查询与可视化系统",
    version="1.0.0"
)

ALLOWED_ORIGINS = [
    "http://43.111.237.98:3000",
    "http://localhost:3000",
]

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
