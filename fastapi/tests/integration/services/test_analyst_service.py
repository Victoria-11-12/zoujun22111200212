import pytest
import json
from app.models import EvaluateRequest, EvalQueryRequest
from app.services.analyst_service import (
    get_analyst_db_connection,
    save_eval_result,
    eval_one,
    evaluate_records_task_async,
    start_evaluation,
    query_results,
    get_results_stats,
    eval_progress,
    eval_lock
)


class TestGetAnalystDbConnection:
    """分析师数据库连接测试"""

    @pytest.mark.integration
    def test_db_connection(self):
        """测试数据库连接"""
        conn = get_analyst_db_connection()
        assert conn is not None
        conn.close()


class TestSaveEvalResult:
    """保存评估结果测试"""

    @pytest.mark.integration
    def test_save_eval_result(self):
        """测试保存评估结果"""
        save_eval_result(
            source_table="user_chat_logs",
            source_id=1,
            eval_type="response",
            score=4,
            dimensions='{"relevance": 4, "accuracy": 4}',
            issues="",
            verdict="pass",
            user_content="测试问题",
            ai_content="测试回答"
        )
        conn = get_analyst_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM eval_results WHERE source_table='user_chat_logs' AND source_id=1"
            )
            result = cursor.fetchone()
            assert result is not None
        conn.close()


class TestEvalOne:
    """单条记录评估测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_eval_response_type(self):
        """测试对话质量评估"""
        semaphore = __import__('asyncio').Semaphore(5)
        record = {
            "id": 0,
            "source_table": "user_chat_logs",
            "user_content": "这部电影好看吗",
            "ai_content": "这部电影评分很高，值得一看。",
            "created_at": ""
        }
        await eval_one(record, "response", semaphore)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_eval_code_type(self):
        """测试代码质量评估"""
        semaphore = __import__('asyncio').Semaphore(5)
        record = {
            "id": 0,
            "source_table": "chart_generation_logs",
            "question": "绘制票房柱状图",
            "generated_code": "from pyecharts.charts import Bar\nchart = Bar()",
            "is_success": True,
            "error_msg": "",
            "user_content": "绘制票房柱状图",
            "ai_content": "from pyecharts.charts import Bar\nchart = Bar()",
            "created_at": ""
        }
        await eval_one(record, "code", semaphore)


class TestEvaluateRecordsTaskAsync:
    """异步批量评估测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_batch_evaluation(self):
        """测试异步批量评估"""
        records = [
            {
                "id": i,
                "source_table": "user_chat_logs",
                "user_content": f"测试问题{i}",
                "ai_content": f"测试回答{i}",
                "created_at": ""
            }
            for i in range(2)
        ]
        await evaluate_records_task_async(records, "response")
        with eval_lock:
            assert eval_progress["status"] == "done"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_semaphore_concurrency(self):
        """测试信号量并发控制"""
        with eval_lock:
            eval_progress["status"] = "idle"
            eval_progress["total"] = 0
            eval_progress["completed"] = 0
        records = [
            {
                "id": i,
                "source_table": "user_chat_logs",
                "user_content": f"并发测试{i}",
                "ai_content": f"并发回答{i}",
                "created_at": ""
            }
            for i in range(6)
        ]
        await evaluate_records_task_async(records, "response")
        with eval_lock:
            assert eval_progress["completed"] == 6

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_exception_isolation(self):
        """测试异常隔离"""
        with eval_lock:
            eval_progress["status"] = "idle"
            eval_progress["total"] = 0
            eval_progress["completed"] = 0
        records = [
            {
                "id": 9999,
                "source_table": "nonexistent_table",
                "user_content": "",
                "ai_content": "",
                "created_at": ""
            }
        ]
        await evaluate_records_task_async(records, "response")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_status_update(self):
        """测试状态更新"""
        with eval_lock:
            eval_progress["status"] = "idle"
            eval_progress["total"] = 0
            eval_progress["completed"] = 0
        records = [
            {
                "id": i,
                "source_table": "user_chat_logs",
                "user_content": f"状态测试{i}",
                "ai_content": f"状态回答{i}",
                "created_at": ""
            }
            for i in range(2)
        ]
        await evaluate_records_task_async(records, "response")
        with eval_lock:
            assert eval_progress["status"] == "done"
            assert eval_progress["completed"] == 2


class TestStartEvaluation:
    """批量评估任务启动测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_start_normal(self):
        """测试正常启动评估任务"""
        with eval_lock:
            eval_progress["status"] = "idle"
        request = EvaluateRequest(
            tables=[],
            start_date="",
            end_date=""
        )
        result = await start_evaluation(request)
        assert "error" in result, "空记录集应返回错误"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_reject_when_running(self):
        """测试已有任务运行时拒绝"""
        with eval_lock:
            eval_progress["status"] = "running"
        request = EvaluateRequest(
            tables=["user_chat_logs"],
            start_date="",
            end_date=""
        )
        result = await start_evaluation(request)
        assert result == {"error": "已有评估任务正在运行"}
        with eval_lock:
            eval_progress["status"] = "idle"


class TestQueryResults:
    """评估结果查询测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_query_by_table(self):
        """测试按表名查询评估结果"""
        request = EvalQueryRequest(table="user_chat_logs")
        results = await query_results(request)
        assert isinstance(results, (list, tuple))

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_query_with_time_range(self):
        """测试按时间范围查询评估结果"""
        request = EvalQueryRequest(
            table="user_chat_logs",
            start_time="2024-01-01",
            end_time="2030-12-31"
        )
        results = await query_results(request)
        assert isinstance(results, (list, tuple))


class TestGetResultsStats:
    """评估结果统计测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_stats_structure(self):
        """测试统计结果结构"""
        result = await get_results_stats()
        assert isinstance(result, dict)
        if "error" not in result:
            assert "score_distribution" in result
            assert "dimension_avg" in result
            assert "low_score_cases" in result
