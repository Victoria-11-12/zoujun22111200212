###评估Agent

import os
import json
import asyncio
import threading
import pymysql
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.models import ResponseEvalResult, CodeEvalResult


###一、基本配置

# 评估模块专用 LLM
eval_llm = ChatOpenAI(
    model=os.getenv('EVAL_MODEL_NAME'),
    api_key=os.getenv('EVAL_API_KEY'),
    base_url=os.getenv('API_BASE'),
    temperature=0
)

# 分析师数据库连接（只读权限查询日志表，读写权限操作 eval_results 表）
DB_USER_ANALYST = os.getenv('DB_USER_ANALYST')
DB_PASS_ANALYST = os.getenv('DB_PASS_ANALYST')
DB_URI_ANALYST = f"mysql+pymysql://{DB_USER_ANALYST}:{DB_PASS_ANALYST}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"

# 评估进度全局变量
eval_progress = {"status": "idle", "total": 0, "completed": 0}  # 全局字典，记录当前评估状态、总任务数、已完成任务数
eval_lock = threading.Lock()  # 线程锁，防止多线程同时修改进度数据


#二、评估链配置

# 文本类回复评估链
response_eval_prompt = ChatPromptTemplate.from_template("""你是一个 LLM 输出质量评估员。请对以下对话记录进行质量评估。

用户输入：{user_content}
AI 回复：{ai_response}

请从以下维度打分（1-5分）：
1. 相关性：AI 回复是否准确回答了用户的问题
2. 完整性：回复是否包含充分的信息，有无遗漏
3. 准确性：回复中的数据是否正确无误
4. 格式：回复是否清晰易读，结构良好

评分标准：
- 5分：完全符合要求，无任何问题
- 4分：基本符合，有小瑕疵但不影响使用
- 3分：部分符合，有明显不足
- 2分：严重不足，影响使用
- 1分：完全不符合，答非所问或数据错误

verdict 规则：
- score >= 4：pass
- score == 3：review
- score <= 2：fail

请只输出 JSON，不要其他内容，格式如下：
{{
    "score": <整数1-5>,
    "dimensions": {{
        "relevance": <整数1-5>,
        "completeness": <整数1-5>,
        "accuracy": <整数1-5>,
        "format": <整数1-5>
    }},
    "issues": "<问题描述>",
    "verdict": "<pass/review/fail>"
}}""")

response_eval_chain = response_eval_prompt | eval_llm.with_structured_output(
    ResponseEvalResult,
    method="json_mode"
)

# 代码类评估链
code_eval_prompt = ChatPromptTemplate.from_template("""你是一个代码质量评估员。请评估以下 pyecharts 绘图代码的质量。

用户需求：{question}
生成的代码：{code}
执行结果：{exec_result}

请从以下维度打分（1-5分）：
1. 可运行性：代码是否能正确执行并生成图表
2. 图表完整性：是否包含标题、坐标轴名称
3. 工具箱：是否包含 ToolboxOpts（用户可下载图片）
4. 单位标注：坐标轴是否有单位说明（如"票房（万美元）"）
5. 类型匹配：图表类型是否符合用户需求（如趋势用折线图、对比用柱状图）

评分标准：
- 5分：完全符合要求
- 4分：基本符合，有小瑕疵
- 3分：部分符合，有明显不足
- 2分：严重不足
- 1分：完全不符合

verdict 规则：
- score >= 4：pass
- score == 3：review
- score <= 2：fail

请只输出 JSON，不要其他内容，格式如下：
{{
    "score": <整数1-5>,
    "dimensions": {{
        "runnable": <整数1-5>,
        "chart_completeness": <整数1-5>,
        "toolbox": <整数1-5>,
        "unit_label": <整数1-5>,
        "chart_type_match": <整数1-5>
    }},
    "issues": "<问题描述>",
    "verdict": "<pass/review/fail>"
}}""")

code_eval_chain = code_eval_prompt | eval_llm.with_structured_output(
    CodeEvalResult,
    method="json_mode"
)


#三、数据库配置
def get_analyst_db_connection():
    """获取分析师数据库连接（只读权限）"""
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=DB_USER_ANALYST,
        password=DB_PASS_ANALYST,
        database=os.getenv('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor
    )


def save_eval_result(source_table: str,
                     source_id: int,
                     eval_type: str,
                     score: int,
                     dimensions: str,
                     issues: str,
                     verdict: str,
                     user_content: str = "",
                     ai_content: str = "",
                     created_at: str = ""):
    """保存评估结果到 eval_results 表"""
    try:
        conn = get_analyst_db_connection()
        with conn.cursor() as cursor:
            if not created_at:
                cursor.execute("SELECT NOW()")
                result = cursor.fetchone()
                if result:
                    created_at = result[0]
                    if hasattr(created_at, 'strftime'):
                        created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute(
                """INSERT INTO eval_results
                    (source_table, source_id, eval_type, user_content, ai_content, score, dimensions, issues, verdict, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (source_table, source_id, eval_type, user_content, ai_content, score, dimensions, issues, verdict, created_at)
            )
            conn.commit()
            print(f"[保存成功] {source_table} id={source_id}, score={score}")
    except Exception as e:
        print(f"[保存失败] {source_table} id={source_id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


# 四、评估执行函数

async def eval_one(record: dict, eval_type: str, semaphore: asyncio.Semaphore):
    """评估单条记录的独立函数
    
    Args:
        record: 待评估的记录字典
        eval_type: 评估类型，'response' 或 'code'
        semaphore: 并发控制信号量
    """
    async with semaphore:
        try:
            if eval_type == "response":
                result = await response_eval_chain.ainvoke({
                    "user_content": record.get("user_content", ""),
                    "ai_response": record.get("ai_content", "")
                })

            elif eval_type == "code":
                exec_result = json.dumps({
                    "success": record.get("is_success", False),
                    "error": record.get("error_msg", "")
                }, ensure_ascii=False)

                result = await code_eval_chain.ainvoke({
                    "question": record.get("question", ""),
                    "code": record.get("generated_code", ""),
                    "exec_result": exec_result
                })
            
            save_eval_result(
                source_table=record.get("source_table", ""),
                source_id=record.get("id", 0),
                eval_type=eval_type,
                score=result.score,
                dimensions=json.dumps(result.dimensions, ensure_ascii=False),
                issues=result.issues,
                verdict=result.verdict,
                user_content=record.get("user_content", ""),
                ai_content=record.get("ai_content", ""),
                created_at=record.get("created_at", "")
            )
        except Exception as e:
            print(f"评估失败 (id={record.get('id')}): {e}")
            save_eval_result(
                source_table=record.get("source_table", ""),
                source_id=record.get("id", 0),
                eval_type=eval_type,
                score=0,
                dimensions="{}",
                issues=f"评估失败: {str(e)}",
                verdict="fail",
                user_content=record.get("user_content", ""),
                ai_content=record.get("ai_content", ""),
                created_at=record.get("created_at", "")
            )
        finally:
            with eval_lock:
                eval_progress["completed"] += 1


async def evaluate_records_task_async(records: list, eval_type: str):
    """异步执行评估任务
    
    Args:
        records: 待评估的记录列表，每条记录包含用户对话或代码执行信息
        eval_type: 评估类型，'response' 对话评估或 'code' 代码评估
    """
    global eval_progress

    semaphore = asyncio.Semaphore(5)
    
    await asyncio.gather(*[eval_one(r, eval_type, semaphore) for r in records])
    
    with eval_lock:
        eval_progress["status"] = "done"


#五、结构定义

class EvaluateRequest(BaseModel):
    tables: list[str] = Field(default=["user_chat_logs", "admin_chat_logs", "chart_generation_logs", "security_warning_logs"])
    start_date: str = Field(default="")
    end_date: str = Field(default="")


#六、接口

async def start_evaluation(request: EvaluateRequest):
    """启动质量评估任务"""
    global eval_progress
    
    with eval_lock:
        if eval_progress["status"] == "running":
            return {"error": "已有评估任务正在运行"}
    
    try:
        conn = get_analyst_db_connection()
        all_records = []
        
        with conn.cursor() as cursor:
            date_filter = ""
            params = []

            if request.start_date and request.end_date:
                date_filter = " AND DATE(created_at) BETWEEN %s AND %s"
                params = [request.start_date, request.end_date]
            
            for table in request.tables:
                if table in ["user_chat_logs", "admin_chat_logs", "security_warning_logs"]:
                    cursor.execute(f"""
                        SELECT id, session_id, role, content, created_at, '{table}' as source_table
                        FROM {table}
                        WHERE 1=1 {date_filter}
                        ORDER BY id
                    """, params)
                    records = cursor.fetchall()
                    sessions = {}
                    for r in records:
                        sid = r["session_id"]
                        if sid not in sessions:
                            sessions[sid] = []
                        sessions[sid].append(r)
                    
                    for sid, session_records in sessions.items():
                        for i, r in enumerate(session_records):
                            if r["role"] == "ai" and i > 0:
                                user_record = session_records[i-1]
                                if user_record["role"] == "user":
                                    all_records.append({
                                        "id": r["id"],
                                        "source_table": table,
                                        "user_content": user_record["content"],
                                        "ai_content": r["content"],
                                        "eval_type": "response",
                                        "created_at": r["created_at"]
                                    })
                
                elif table == "chart_generation_logs":
                    cursor.execute(f"""
                        SELECT id, question, sql_result, generated_code, is_success, error_msg, created_at, '{table}' as source_table
                        FROM {table}
                        WHERE 1=1 {date_filter}
                        ORDER BY id
                    """, params)
                    records = cursor.fetchall()
                    for r in records:
                        all_records.append({
                            "id": r["id"],
                            "source_table": table,
                            "question": r["question"],
                            "sql_result": r["sql_result"],
                            "generated_code": r["generated_code"],
                            "is_success": r["is_success"],
                            "error_msg": r["error_msg"],
                            "user_content": r["question"],
                            "ai_content": r["generated_code"],
                            "eval_type": "code",
                            "created_at": r["created_at"]
                        })
        
        conn.close()

        if not all_records:
            return {"error": "没有找到符合条件的记录"}
        
        eval_tasks = []
        for record in all_records:
            eval_type = record.pop("eval_type")
            eval_tasks.append((record, eval_type))
        
        response_records = [r for r, t in eval_tasks if t == "response"]
        code_records = [r for r, t in eval_tasks if t == "code"]
        
        with eval_lock:
            eval_progress["status"] = "running"
            eval_progress["total"] = len(all_records)
            eval_progress["completed"] = 0

        def run_evaluation():
            if response_records:
                asyncio.run(evaluate_records_task_async(response_records, "response"))
            if code_records:
                asyncio.run(evaluate_records_task_async(code_records, "code"))
            with eval_lock:
                eval_progress["status"] = "done"

        thread = threading.Thread(target=run_evaluation)
        thread.start()

        return {"message": "评估任务已启动", "total": len(all_records)}

    except Exception as e:
        import traceback
        traceback.print_exc()
        with eval_lock:
            eval_progress["status"] = "error"
        return {"error": str(e)}


async def get_eval_progress():
    """获取评估进度"""
    global eval_progress
    with eval_lock:
        return eval_progress.copy()


async def query_eval_results(request):
    """查询评估结果"""
    conn = get_analyst_db_connection()
    try:
        with conn.cursor() as cursor:
            where_clauses = []
            params = []
            
            if request.table:
                where_clauses.append("source_table = %s")
                params.append(request.table)
            if request.start_time:
                where_clauses.append("created_at >= %s")
                params.append(request.start_time)
            if request.end_time:
                where_clauses.append("created_at <= %s")
                params.append(request.end_time)
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            cursor.execute(f"""
                SELECT * FROM eval_results
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT 100
            """, params)
            
            results = cursor.fetchall()
            return results
    finally:
        conn.close()
