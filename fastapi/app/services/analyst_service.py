# 评估服务
# 处理质量评估业务逻辑

import os
import json
import asyncio
import threading
import pymysql
from app.models import EvalQueryRequest, EvaluateRequest
from app.chains.eval_chains import response_eval_chain, code_eval_chain
from app.config import engine_analyst


# 评估进度全局变量
eval_progress = {"status": "idle", "total": 0, "completed": 0}
eval_lock = threading.Lock()


# 数据库连接函数
# 说明：评估模块使用连接池获取数据库连接
# 原因：
#   1. 需要同时查询多个表（user_chat_logs, admin_chat_logs, chart_generation_logs 等）
#   2. 需要执行复杂的关联查询和会话匹配逻辑
#   3. 需要插入数据到 eval_results 表
# 其他 Agent（sql_agent, admin_agent）本身不直接连接数据库，而是通过 tools/ 中的工具函数操作
def get_analyst_db_connection():
    """获取分析师数据库连接（只读权限），使用连接池"""
    conn = engine_analyst.raw_connection()
    # pymysql 连接需要设置 cursorclass 才能返回字典格式
    conn.cursorclass = pymysql.cursors.DictCursor
    return conn


# 保存评估结果到 eval_results 表
# 说明：将评估分数、维度评分、问题描述等保存到数据库，用于后续分析和展示
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


# 评估单条记录
async def eval_one(record: dict, eval_type: str, semaphore: asyncio.Semaphore):
    """评估单条记录的独立函数"""
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


# 异步执行评估任务
async def evaluate_records_task_async(records: list, eval_type: str):
    """异步执行评估任务"""
    global eval_progress
    semaphore = asyncio.Semaphore(5)
    await asyncio.gather(*[eval_one(r, eval_type, semaphore) for r in records])
    with eval_lock:
        eval_progress["status"] = "done"


# 启动质量评估任务
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


# 获取评估进度
async def get_progress():
    """获取评估进度"""
    global eval_progress
    with eval_lock:
        return eval_progress.copy()


# 查询评估结果
async def query_results(request: EvalQueryRequest):
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
