import pytest
import json

pytestmark = pytest.mark.token_measure


def _get_token_usage(result, label=""):
    """从调用结果中提取 token 用量"""
    usage = getattr(result, 'usage_metadata', None)
    if usage:
        inp = usage.get('input_tokens', 0)
        out = usage.get('output_tokens', 0)
        total = usage.get('total_tokens', 0)
        print(f"    [{label}]  input={inp}  output={out}  total={total}")
        return total
    else:
        print(f"    [{label}]  [!] 未获取到 usage_metadata")
        return 0


@pytest.mark.token_measure
class TestUserQueryToken:
    """场景1：普通用户查询电影 - token 消耗测量"""

    @pytest.mark.asyncio
    async def test_user_query(self):
        from app.chains.user_chains import intent_chain, wrap_chain
        from app.agents.sql_agent import sql_executor

        message = "查询周星驰主演的电影有哪些"
        history = []
        total = 0

        print("\n--- 步骤1: 意图判断 ---")
        intent_result = await intent_chain.ainvoke({"message": message})
        intent = intent_result.content.strip().upper()
        total += _get_token_usage(intent_result, "意图链")
        print(f"    意图: {intent}")

        print("\n--- 步骤2: SQL Agent ---")
        sql_result = await sql_executor.ainvoke({"input": message})
        sql_output = sql_result.get('output', '')
        print(f"    SQL Agent 查询完成, 结果长度: {len(sql_output)}")
        # 注：AgentExecutor 返回 dict，不直接带 usage_metadata

        print("\n--- 步骤3: 包装链回复 ---")
        reply_result = await wrap_chain.ainvoke({
            "question": message, "result": sql_output, "history": history
        })
        total += _get_token_usage(reply_result, "包装链")

        print(f"\n  >>> 用户查询 可统计 token: {total}")
        assert total > 0, "应该有 token 消耗"


@pytest.mark.token_measure
class TestAdminToken:
    """场景2：管理员操作 - token 消耗测量"""

    @pytest.mark.asyncio
    async def test_admin_operations(self):
        from app.agents.admin_agent import admin_executor
        from app.tools.admin_tools import set_current_admin_name

        set_current_admin_name("admin_test")
        total = 0

        print("\n--- 步骤1: 新增用户 testuser ---")
        r1 = await admin_executor.ainvoke({"input": "新增一个用户，用户名 testuser，密码 123456，角色 user"})
        print(f"    回复: {r1.get('output', '')[:80]}...")

        print("\n--- 步骤2: 删除用户 testuser ---")
        r2 = await admin_executor.ainvoke({"input": "删除用户 testuser"})
        print(f"    回复: {r2.get('output', '')[:80]}...")

        print("\n--- 步骤3: 回滚操作 ---")
        r3 = await admin_executor.ainvoke({"input": "回滚我刚才的删除操作"})
        print(f"    回复: {r3.get('output', '')[:80]}...")

        # 注：AgentExecutor 返回 dict，LLM 调用在内部分多次进行，
        # 无法从最终 dict 获取 usage_metadata
        print(f"\n  >>> 管理员操作 可统计 token: {total}")
        print(f"      注：AgentExecutor 内部多次 LLM 调用，返回结果不暴露 usage_metadata")


@pytest.mark.token_measure
class TestChartToken:
    """场景3：图表生成 - token 消耗测量"""

    @pytest.mark.asyncio
    async def test_chart_generation(self):
        from app.chains.chart_chains import chart_intent_chain, python_chart_chain
        from app.agents.sql_agent import sql_executor

        question = "各年份电影数量趋势图"
        total = 0

        print("\n--- 步骤1: 图表意图判断 ---")
        intent_result = await chart_intent_chain.ainvoke({"question": question})
        intent = intent_result.content.strip().upper()
        total += _get_token_usage(intent_result, "图表意图链")
        print(f"    意图: {intent}")

        if "NOT_CHART" not in intent:
            print("\n--- 步骤2: SQL Agent ---")
            sql_result = await sql_executor.ainvoke({"input": question})
            sql_output = sql_result.get('output', '')
            print(f"    SQL Agent 查询完成, 结果长度: {len(sql_output)}")

            print("\n--- 步骤3: Python 代码生成 ---")
            code_result = await python_chart_chain.ainvoke({
                "question": question, "data": sql_output, "feedback": ""
            })
            total += _get_token_usage(code_result, "Python代码链")

        print(f"\n  >>> 图表生成 可统计 token: {total}")
        assert total > 0, "应该有 token 消耗"


@pytest.mark.token_measure
class TestEvalToken:
    """场景4：评估 - token 消耗测量"""

    @pytest.mark.asyncio
    async def test_eval_response(self):
        from app.chains.eval_chains import response_eval_chain

        total = 0

        print("\n--- 步骤1: 文本回复评估 ---")
        eval_result = await response_eval_chain.ainvoke({
            "user_content": "查询周星驰主演的电影有哪些",
            "ai_response": "周星驰主演的电影有：\n1. 功夫\n2. 喜剧之王\n3. 大话西游\n4. 逃学威龙\n5. 食神"
        })
        total += _get_token_usage(eval_result, "回复评估链")
        print(f"    评分: {eval_result.score}, verdict: {eval_result.verdict}")

        print(f"\n  >>> 评估 可统计 token: {total}")
        assert total > 0, "应该有 token 消耗"

    @pytest.mark.asyncio
    async def test_eval_code(self):
        from app.chains.eval_chains import code_eval_chain

        code = """
import pandas as pd
from pyecharts.charts import Bar
from pyecharts import options as opts
data = pd.DataFrame({'year': [2000,2001,2002], 'count': [5,8,12]})
chart = Bar()
chart.add_xaxis(data['year'].tolist())
chart.add_yaxis("数量", data['count'].tolist())
chart.set_global_opts(title_opts=opts.TitleOpts(title="趋势"),
    xaxis_opts=opts.AxisOpts(name="年份"),
    yaxis_opts=opts.AxisOpts(name="数量"),
    toolbox_opts=opts.ToolboxOpts())
html = chart.render_embed()
print("CHART_HTML_START")
print(html)
print("CHART_HTML_END")
"""
        total = 0

        print("\n--- 步骤1: 代码质量评估 ---")
        eval_result = await code_eval_chain.ainvoke({
            "question": "各年份电影数量趋势图",
            "code": code,
            "exec_result": json.dumps({"success": True, "error": ""})
        })
        total += _get_token_usage(eval_result, "代码评估链")
        print(f"    评分: {eval_result.score}, verdict: {eval_result.verdict}")
        print(f"    issues: {eval_result.issues[:100]}")

        print(f"\n  >>> 代码评估 可统计 token: {total}")
        assert total > 0, "应该有 token 消耗"
