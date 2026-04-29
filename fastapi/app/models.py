from pydantic import BaseModel, Field
from typing import Dict, Optional, TypedDict, List


class ChatRequest(BaseModel):
    message: str
    sessionId: str = ""
    username: str = ""


class AdminChatRequest(BaseModel):
    message: str
    sessionId: str = ""
    username: str = ""


class ChartRequest(BaseModel):
    message: str
    sessionId: str = ""
    username: str = ""


class EvalQueryRequest(BaseModel):
    table: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class ChartGraphState(TypedDict, total=False):
    question: str
    session_id: str
    user_name: str
    sql_result: str
    code_raw: str
    code: str
    feedback: str
    eval_pass: bool
    attempts: int
    chart_html: str
    error: str


class ResponseEvalResult(BaseModel):
    score: int = Field(description="总分1-5")
    dimensions: dict = Field(description='{"相关性":5,"完整性":4,"准确性":3,"格式":5}')
    issues: str = Field(description="问题描述")
    verdict: str = Field(description="pass/review/fail")


class CodeEvalResult(BaseModel):
    score: int = Field(description="总分1-5")
    dimensions: dict = Field(description='{"代码正确性":5,"可视化效果":4,"安全性":5}')
    issues: str = Field(description="问题描述")
    verdict: str = Field(description="pass/review/fail")
