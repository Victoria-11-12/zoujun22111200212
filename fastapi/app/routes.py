import os
import json
import uuid
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.models import ChatRequest, AdminChatRequest, ChartRequest, EvalQueryRequest
from app.config import llm
from app.history import get_history, save_history
from app.logs import log_user_chat, log_admin_chat, log_security_warning
from app.sql_agent import sql_executor
from app.chains import intent_chain, direct_chain, warning_chain, sql_reply_chain, chart_intent_chain, chart_not_chain
from app.admin import admin_executor, check_sql_safety
from app.chart_graph import chart_graph
from app.eval_module import (
    eval_progress, eval_one, evaluate_records_task_async,
    get_analyst_db_connection, save_eval_result
)

router = APIRouter()


@router.post("/api/ai/stream")
async def ai_chat_stream(request: Request, chat_request: ChatRequest):
    user_message = chat_request.message
    session_id = chat_request.sessionId
    user_name = chat_request.username
    client_ip = request.client.host

    intent = await intent_chain.ainvoke({"question": user_message})
    intent = intent.strip().upper()

    async def generate():
        try:
            if "WARNING" in intent:
                log_security_warning(session_id, user_name, client_ip, "user", user_message, "意图路由检测")
                log_user_chat(session_id, "user", user_message, "WARNING", user_name)
                reply = ''
                async for chunk in warning_chain.astream({"question": user_message}):
                    reply += chunk
                    yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                log_user_chat(session_id, "ai", reply, "WARNING", user_name)
                return

            log_user_chat(session_id, "user", user_message, intent, user_name)

            if "DIRECT_REPLY" in intent:
                history = get_history(session_id)
                reply = ''
                async for chunk in direct_chain.astream({"question": user_message, "history": history}):
                    reply += chunk
                    yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                save_history(session_id, user_message, reply)
                log_user_chat(session_id, "ai", reply, "DIRECT_REPLY", user_name)
                return

            if "NEED_SQL" in intent:
                history = get_history(session_id)
                result = await sql_executor.ainvoke({
                    "input": user_message,
                    "chat_history": history
                })
                sql_result = result.get("output", "")
                reply = ''
                async for chunk in sql_reply_chain.astream({"question": user_message, "result": sql_result, "history": history}):
                    reply += chunk
                    yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                save_history(session_id, user_message, reply)
                log_user_chat(session_id, "ai", reply, "NEED_SQL", user_name)
                return
        except Exception as e:
            print(f"AI 普通用户接口报错: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.post("/api/admin/ai/stream")
async def admin_chat_stream(request: Request, chat_request: AdminChatRequest):
    user_message = chat_request.message
    session_id = chat_request.sessionId
    user_name = chat_request.username
    client_ip = request.client.host

    is_safe, warning = check_sql_safety(user_message)
    if not is_safe:
        log_security_warning(session_id, user_name, client_ip, "user", user_message, "系统警告回复")
        log_admin_chat(session_id, "user", user_message, user_name)
        log_admin_chat(session_id, "ai", warning, user_name)
        async def warning_stream():
            yield f"data: {json.dumps({'content': f'安全警告: {warning}'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(
            warning_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )

    log_admin_chat(session_id, "user", user_message, user_name)

    async def generate():
        try:
            result = await admin_executor.ainvoke({
                "input": user_message,
                "chat_history": []
            })
            agent_reply = result.get('output', '')
            for i in range(0, len(agent_reply), 10):
                chunk = agent_reply[i:i + 10]
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            save_history(session_id, user_message, agent_reply)
            log_admin_chat(session_id, "ai", agent_reply, user_name)
        except Exception as e:
            print(f"AI 管理员接口报错: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.post("/api/chart/generate")
async def chart_generate(request: ChartRequest):
    chart_message = request.message
    session_id = request.sessionId
    user_name = request.username

    intent = await chart_intent_chain.ainvoke({"question": chart_message})
    intent = intent.strip().upper()
    print(f"绘图意图判断: {intent}, 问题: {chart_message}")

    async def generate():
        try:
            if "NOT_CHART" in intent:
                reply = await chart_not_chain.ainvoke({"question": chart_message})
                yield f"data: {json.dumps({'type': 'text', 'content': reply}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                return

            result = await chart_graph.ainvoke({
                "question": chart_message,
                "session_id": session_id,
                "user_name": user_name,
                "feedback": "",
                "attempts": 0,
            })

            if result.get("chart_html"):
                yield f"data: {json.dumps({'type': 'chart', 'chart_html': result['chart_html']}, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'text', 'content': result.get('error', '图表生成失败')}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            print(f"绘图接口报错: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'text', 'content': str(e)}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.post("/api/eval/start")
async def start_evaluation(request: EvalQueryRequest):
    table = request.table
    start_time = request.start_time
    end_time = request.end_time

    task_id = str(uuid.uuid4())

    try:
        conn = get_analyst_db_connection()
        with conn.cursor() as cursor:
            where_clause = "WHERE 1=1"
            params = []

            if start_time:
                where_clause += " AND created_at >= %s"
                params.append(start_time)
            if end_time:
                where_clause += " AND created_at <= %s"
                params.append(end_time)

            if table == "user_chat_logs":
                cursor.execute(f"""
                    SELECT u1.*, u2.content as ai_content
                    FROM user_chat_logs u1
                    LEFT JOIN user_chat_logs u2 ON u1.session_id = u2.session_id
                    AND u2.role = 'ai' AND u2.created_at > u1.created_at
                    {where_clause} AND u1.role = 'user'
                    ORDER BY u1.created_at DESC
                    LIMIT 100
                """, params)
            elif table == "chart_generation_logs":
                cursor.execute(f"""
                    SELECT * FROM chart_generation_logs
                    {where_clause} AND is_success = 1
                    ORDER BY created_at DESC
                    LIMIT 100
                """, params)
            else:
                return {"error": "不支持的表名"}

            records = cursor.fetchall()

    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

    eval_type = "response" if table == "user_chat_logs" else "code"

    asyncio.create_task(evaluate_records_task_async(task_id, table, records, eval_type))

    return {"task_id": task_id, "total": len(records)}


@router.get("/api/eval/progress/{task_id}")
async def get_eval_progress(task_id: str):
    progress = eval_progress.get(task_id, {})
    return {
        "status": progress.get("status", "unknown"),
        "total": progress.get("total", 0),
        "completed": progress.get("completed", 0),
        "current": progress.get("current", "")
    }


@router.post("/api/eval/results")
async def get_eval_results(request: EvalQueryRequest):
    table = request.table
    start_time = request.start_time
    end_time = request.end_time

    try:
        conn = get_analyst_db_connection()
        with conn.cursor() as cursor:
            where_clause = "WHERE source_table = %s"
            params = [table]

            if start_time:
                where_clause += " AND created_at >= %s"
                params.append(start_time)
            if end_time:
                where_clause += " AND created_at <= %s"
                params.append(end_time)

            cursor.execute(f"""
                SELECT score, COUNT(*) as count
                FROM eval_results
                {where_clause}
                GROUP BY score
                ORDER BY score
            """, params)
            score_distribution = cursor.fetchall()

            cursor.execute(f"""
                SELECT dimensions FROM eval_results
                {where_clause}
            """, params)
            all_dimensions = cursor.fetchall()

            dimension_avg = {}
            dimension_counts = {}
            for row in all_dimensions:
                try:
                    dims = json.loads(row['dimensions'])
                    for dim_name, dim_score in dims.items():
                        if dim_name not in dimension_avg:
                            dimension_avg[dim_name] = 0
                            dimension_counts[dim_name] = 0
                        dimension_avg[dim_name] += dim_score
                        dimension_counts[dim_name] += 1
                except:
                    pass

            for dim_name in dimension_avg:
                if dimension_counts[dim_name] > 0:
                    dimension_avg[dim_name] = round(dimension_avg[dim_name] / dimension_counts[dim_name], 2)

            cursor.execute(f"""
                SELECT er.*, 
                       ucl.content as user_content,
                       ucl2.content as ai_content
                FROM eval_results er
                LEFT JOIN user_chat_logs ucl ON er.source_table = 'user_chat_logs' AND er.source_id = ucl.id
                LEFT JOIN user_chat_logs ucl2 ON er.source_table = 'user_chat_logs' AND er.source_id = ucl2.id AND ucl2.role = 'ai'
                {where_clause} AND er.score <= 3
                ORDER BY er.score ASC
                LIMIT 50
            """, params)
            low_score_cases = cursor.fetchall()

            return {
                "score_distribution": [{"score": row["score"], "count": row["count"]} for row in score_distribution],
                "dimension_avg": dimension_avg,
                "low_score_cases": [
                    {
                        "id": row["id"],
                        "source_table": row["source_table"],
                        "score": row["score"],
                        "issues": row["issues"],
                        "user_content": row.get("user_content", ""),
                        "ai_content": row.get("ai_content", "")
                    }
                    for row in low_score_cases
                ]
            }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
