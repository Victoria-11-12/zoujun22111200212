import os
import json
import asyncio
import pymysql
from typing import Dict, Optional
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.config import MODEL_NAME
from app.models import ResponseEvalResult, CodeEvalResult


eval_progress: Dict[str, any] = {}
eval_lock = asyncio.Lock()

eval_llm = ChatOpenAI(
    model=os.getenv('MODEL_NAME'),
    openai_api_key=os.getenv('API_KEY'),
    openai_api_base=os.getenv('API_BASE'),
    temperature=0.1,
    extra_body={"thinking": {"type": "disabled"}}
)

DB_URI_ANALYST = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"


response_eval_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个对话质量评估专家。请评估AI回复的质量。

评分维度（1-5分）：
1. 相关性：回复是否与用户问题相关
2. 完整性：回复是否完整回答了问题
3. 准确性：信息是否准确无误
4. 格式：格式是否清晰易读

请输出JSON格式：
{{
    "score": 总分1-5,
    "dimensions": {{"相关性": 5, "完整性": 4, "准确性": 3, "格式": 5}},
    "issues": "存在的问题描述",
    "verdict": "pass/review/fail"
}}

verdict标准：
- pass: score >= 4 且无明显问题
- review: score = 3 或有小问题
- fail: score <= 2 或有严重问题"""),
    ("human", "用户问题：{question}\n\nAI回复：{response}")
])

response_eval_chain = response_eval_prompt | eval_llm.with_structured_output(ResponseEvalResult)


code_eval_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个代码质量评估专家。请评估生成的Python图表代码质量。

评分维度（1-5分）：
1. 代码正确性：代码是否能正确运行
2. 可视化效果：图表是否美观、清晰
3. 安全性：代码是否安全（无危险操作）

请输出JSON格式：
{{
    "score": 总分1-5,
    "dimensions": {{"代码正确性": 5, "可视化效果": 4, "安全性": 5}},
    "issues": "存在的问题描述",
    "verdict": "pass/review/fail"
}}

verdict标准：
- pass: score >= 4 且代码能正常运行
- review: score = 3 或有小问题
- fail: score <= 2 或有严重错误"""),
    ("human", "用户需求：{question}\n\n生成的代码：\n{code}")
])

code_eval_chain = code_eval_prompt | eval_llm.with_structured_output(CodeEvalResult)


def get_analyst_db_connection():
    """获取分析师数据库连接"""
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        database=os.getenv('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor
    )


def save_eval_result(source_table: str, source_id: int, eval_type: str, result: dict) -> bool:
    """保存评估结果到数据库"""
    try:
        conn = get_analyst_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO eval_results 
                (source_table, source_id, eval_type, score, dimensions, issues, verdict, model_name, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                score = VALUES(score),
                dimensions = VALUES(dimensions),
                issues = VALUES(issues),
                verdict = VALUES(verdict),
                model_name = VALUES(model_name),
                created_at = VALUES(created_at)
            """, (
                source_table, source_id, eval_type,
                result.get('score'), json.dumps(result.get('dimensions', {})),
                result.get('issues'), result.get('verdict'),
                MODEL_NAME, datetime.now()
            ))
            conn.commit()
        return True
    except Exception as e:
        print(f"保存评估结果失败: {e}")
        return False
    finally:
        conn.close()


async def eval_one(record: dict, eval_type: str = "response") -> dict:
    """评估单条记录"""
    try:
        if eval_type == "response":
            result = await response_eval_chain.ainvoke({
                "question": record.get('content', ''),
                "response": record.get('ai_content', '')
            })
        else:
            result = await code_eval_chain.ainvoke({
                "question": record.get('question', ''),
                "code": record.get('generated_code', '')
            })
        
        return {
            "score": result.score,
            "dimensions": result.dimensions,
            "issues": result.issues,
            "verdict": result.verdict
        }
    except Exception as e:
        return {
            "score": 0,
            "dimensions": {},
            "issues": f"评估失败: {str(e)}",
            "verdict": "fail"
        }


async def evaluate_records_task_async(task_id: str, table: str, records: list, eval_type: str = "response"):
    """异步评估任务"""
    global eval_progress
    
    async with eval_lock:
        eval_progress[task_id] = {
            "status": "running",
            "total": len(records),
            "completed": 0,
            "current": ""
        }
    
    try:
        for i, record in enumerate(records):
            async with eval_lock:
                eval_progress[task_id]["current"] = f"正在评估记录 {i+1}/{len(records)}"
            
            result = await eval_one(record, eval_type)
            
            source_id = record.get('id')
            save_eval_result(table, source_id, eval_type, result)
            
            async with eval_lock:
                eval_progress[task_id]["completed"] = i + 1
        
        async with eval_lock:
            eval_progress[task_id]["status"] = "completed"
            eval_progress[task_id]["current"] = "评估完成"
            
    except Exception as e:
        async with eval_lock:
            eval_progress[task_id]["status"] = "error"
            eval_progress[task_id]["current"] = f"错误: {str(e)}"
