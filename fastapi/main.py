import os

os.environ['DOCKER_HOST'] = 'npipe:////./pipe/docker_engine'

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers import user, admin, chart, analyst

load_dotenv()

app = FastAPI(
    title="电影数据分析系统",
    description="基于LangChain和LangGraph的智能电影数据查询与可视化系统",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router, prefix="/api", tags=["用户"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理员"])
app.include_router(chart.router, prefix="/api/chart", tags=["图表"])
app.include_router(analyst.router, prefix="/api/analyst", tags=["评估"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
