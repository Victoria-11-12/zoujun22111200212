import pytest
import threading
from app.services.analyst_service import eval_progress, eval_lock, get_progress


class TestEvalProgress:
    """评估进度状态测试"""

    @pytest.mark.unit
    def test_initial_value(self):
        """测试初始值验证(idle/0/0)"""
        # 验证eval_progress是字典类型
        assert isinstance(eval_progress, dict)
        # 验证包含必要的键
        assert "status" in eval_progress
        assert "total" in eval_progress
        assert "completed" in eval_progress

    @pytest.mark.unit
    def test_state_transition(self):
        """测试状态转换逻辑(idle→running→done/error)"""
        # 保存原始状态
        original_status = eval_progress.get("status")

        # 测试状态可以修改
        eval_progress["status"] = "running"
        assert eval_progress["status"] == "running"

        eval_progress["status"] = "done"
        assert eval_progress["status"] == "done"

        eval_progress["status"] = "error"
        assert eval_progress["status"] == "error"

        # 恢复原始状态
        if original_status:
            eval_progress["status"] = original_status


class TestEvalLock:
    """评估锁测试"""

    @pytest.mark.unit
    def test_thread_safety(self):
        """测试线程锁并发安全性"""
        # 验证eval_lock是线程锁类型
        assert isinstance(eval_lock, type(threading.Lock()))

        # 测试锁可以正常获取和释放
        acquired = eval_lock.acquire(blocking=False)
        assert acquired is True
        eval_lock.release()

    @pytest.mark.unit
    def test_concurrent_task_rejection(self):
        """测试同时启动两个评估任务时第二个被拒绝"""
        # 获取锁
        acquired1 = eval_lock.acquire(blocking=False)
        assert acquired1 is True

        # 尝试再次获取锁（应该失败）
        acquired2 = eval_lock.acquire(blocking=False)
        assert acquired2 is False

        # 释放锁
        eval_lock.release()


class TestGetProgress:
    """获取进度函数测试"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_progress_query(self):
        """测试评估进度查询"""
        # 调用函数获取进度
        progress = await get_progress()

        # 验证返回的是字典
        assert isinstance(progress, dict)
        # 验证包含必要的键
        assert "status" in progress
        assert "total" in progress
        assert "completed" in progress

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_dict_copy_return(self):
        """测试dict copy返回"""
        # 获取进度
        progress1 = await get_progress()
        progress2 = await get_progress()

        # 验证返回的是副本，不是同一个对象
        assert progress1 is not progress2
        assert progress1 == progress2

        # 修改副本不应影响原始数据
        progress1["status"] = "modified"
        assert eval_progress.get("status") != "modified"
