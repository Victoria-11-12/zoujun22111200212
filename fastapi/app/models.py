from pydantic import BaseModel, Field
from typing import Optional


# 请求模型 - 用于API接口参数校验


class ChatRequest(BaseModel):  # 用户聊天请求模型 - routers/user.py, services/user_service.py - /api/ai/stream 接口接收用户对话请求
    message: str  # 必填，用户输入的问题
    sessionId: str = ""  # 可选，会话ID
    username: str = ""  # 可选，用户名
    clientIp: str = ""  # 可选，客户端IP地址


class AdminChatRequest(BaseModel):  # 管理员聊天请求模型 - routers/admin.py, services/admin_service.py - /api/admin/ai/stream 接口接收管理员对话请求
    message: str
    sessionId: str = ""
    username: str = ""
    clientIp: str = ""  # 客户端IP地址


class ChartRequest(BaseModel):  # 图表生成请求模型 - routers/chart.py, services/chart_service.py - /api/chart/generate 接口接收图表生成请求
    message: str
    sessionId: str = ""
    username: str = ""


class EvaluateRequest(BaseModel):  # 启动评估任务请求模型 - routers/analyst.py, services/analyst_service.py - /api/analyst/evaluate 接口启动质量评估
    tables: list[str] = Field(default=["user_chat_logs", "admin_chat_logs", "chart_generation_logs", "security_warning_logs"])
    start_date: str = Field(default="")
    end_date: str = Field(default="")


class EvalQueryRequest(BaseModel):  # 评估结果查询请求模型 - routers/analyst.py, services/analyst_service.py - /api/analyst/query 接口查询评估结果
    table: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class ResponseEvalResult(BaseModel):  # 对话评估结果模型 - agents/eval_agent.py - 评估Agent对用户对话回复进行质量评分
    score: int = Field(description="总分1-5")
    dimensions: dict = Field(description='{"相关性":5,"完整性":4,"准确性":3,"格式":5}')
    issues: str = Field(description="问题描述")
    verdict: str = Field(description="pass/review/fail")


class CodeEvalResult(BaseModel):  # 代码评估结果模型 - agents/eval_agent.py - 评估Agent对图表生成代码进行质量评分
    score: int = Field(description="总分1-5")
    dimensions: dict = Field(description='{"可运行性":5,"图表完整性":4,"工具箱":3,"单位标注":5,"类型匹配":4}')
    issues: str = Field(description="问题描述")
    verdict: str = Field(description="pass/review/fail")
