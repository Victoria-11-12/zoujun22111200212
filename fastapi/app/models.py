from pydantic import BaseModel, Field
from typing import Dict, Optional, TypedDict, List


#定义请求体的Pydantic模型
#BaseModel会自动验证数据类型，如果参数类型错误会返回错误
class ChatRequest(BaseModel):
    message: str #必填，用户输入的问题
    sessionId: str = "" #可选，会话ID
    username: str = "" #可选，用户名
    clientIp: str = "" #可选，客户端IP地址


class AdminChatRequest(BaseModel):
    message: str
    sessionId: str = ""
    username: str = ""


# 七、图表生成接口

# /api/chart/generate 的请求模型
class ChartRequest(BaseModel):
    message: str
    sessionId: str = ""
    username: str = ""


class EvalQueryRequest(BaseModel):
    table: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None


#二、状态机，共享白板，所有节点共享数据，每个节点都可以读写
# ChartGraphState 定义在所有 LangGraph 节点之间传递的共享状态
class ChartGraphState(TypedDict, total=False):

    question: str # 用户输入
    session_id: str # 会话id
    user_name: str # 用户名

    sql_result: str  # SQLAgent 输出 
    code_raw: str  # pythonagent 生成的原始代码 (可能包含 ```python 标记)
    code: str  # 在沙箱内执行的纯净 Python 代码
    feedback: str  # 用于要求 pythonagent 修改代码的反馈
    eval_pass: bool  # eval 节点是否批准代码
    attempts: int  # 尝试计数器防止无限循环 
    chart_html: str  # 最终 HTML (仅在沙箱执行成功时设置)
    error: str  # # 最终错误消息 (达到最大重试次数或致命错误时设置)


###一、基本配置

##这两个模型用于结构化输出
# 对话评估结果模型
class ResponseEvalResult(BaseModel):
    score: int = Field(description="总分1-5")
    dimensions: dict = Field(description='{"相关性":5,"完整性":4,"准确性":3,"格式":5}')
    issues: str = Field(description="问题描述")
    verdict: str = Field(description="pass/review/fail")

# 绘图评估结果模型
class CodeEvalResult(BaseModel):
    score: int = Field(description="总分1-5")
    dimensions: dict = Field(description='{"可运行性":5,"图表完整性":4,"工具箱":3,"单位标注":5,"类型匹配":4}')
    issues: str = Field(description="问题描述")
    verdict: str = Field(description="pass/review/fail")
