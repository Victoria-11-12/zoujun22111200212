# 图表生成工作流
# 使用LangGraph实现图表生成的多节点流程

import re
import docker
from typing import List, TypedDict
from langgraph.graph import StateGraph, END
from app.agents.sql_agent import sql_executor
from app.chains.chart_chains import python_chart_chain
from app.logs import log_chart_generation


# 状态机，共享白板，所有节点共享数据，每个节点都可以读写
# ChartGraphState 定义在所有 LangGraph 节点之间传递的共享状态
class ChartGraphState(TypedDict, total=False):
    question: str  # 用户输入
    session_id: str  # 会话id
    user_name: str  # 用户名

    sql_result: str  # SQLAgent 输出
    code_raw: str  # pythonagent 生成的原始代码 (可能包含 ```python 标记)
    code: str  # 在沙箱内执行的纯净 Python 代码
    feedback: str  # 用于要求 pythonagent 修改代码的反馈
    eval_pass: bool  # eval 节点是否批准代码
    attempts: int  # 尝试计数器防止无限循环
    chart_html: str  # 最终 HTML (仅在沙箱执行成功时设置)
    error: str  # 最终错误消息 (达到最大重试次数或致命错误时设置)

# 正则从 markdown 输出中提取 Python 代码块
def _extract_python_code_block(text: str) -> str:
    # 首先尝试查找带标记的 Python 代码块
    match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
    # 如果找到，只使用代码块内容
    if match:
        return match.group(1).strip()
    # 否则，回退到完整文本
    return text.strip()


# 静态评估: 仅检查代码是否安全并遵循输出约定
def _static_eval(code: str) -> tuple[bool, List[str], str]:
    issues: List[str] = []

    # 安全通信检测
    if "CHART_HTML" not in code:
        issues.append("Missing CHART_HTML assignment (must use chart.render_embed())")

    if "CHART_HTML_START" not in code or "CHART_HTML_END" not in code:
        issues.append("Missing CHART_HTML_START/CHART_HTML_END markers (stdout extraction needs them)")

    # 允许导入列表
    allowed_imports = {"pyecharts"}

    # 禁止导入列表
    banned_tokens = ["import os","import sys","subprocess","socket","requests","urllib","open(","eval(","exec(","__import__"]

    # 在导入行上强制执行允许列表
    for line in code.splitlines():
        if line.startswith("import "):
            module = line.split()[1].split(".")[0]
            if module not in allowed_imports:
                issues.append(f"Illegal import: {module} (allowed: {sorted(allowed_imports)})")
        if line.startswith("from "):
            module = line.split()[1].split(".")[0]
            if module not in allowed_imports:
                issues.append(f"Illegal from-import: {module} (allowed: {sorted(allowed_imports)})")

    # 检查禁止列表
    for token in banned_tokens:
        if token in code:
            issues.append(f"检测到禁止的令牌: {token}")

    passed = len(issues) == 0

    feedback = ""
    if not passed:
        feedback = "请修复以下问题并重新输出完整代码:\n- " + "\n- ".join(issues)

    return passed, issues, feedback


# 节点1: sqlagent
async def _node_sqlagent(state: ChartGraphState) -> ChartGraphState:
    question = state.get("question", "")
    print(f"[ChartGraph] sqlagent: 开始查询数据库, 问题: {question}")
    result = await sql_executor.ainvoke({"input": question})
    state["sql_result"] = result.get("output", "")
    print(f"[ChartGraph] sqlagent: 查询完成, 结果长度: {len(state['sql_result'])}")
    return state


# 节点2: pythonagent
async def _node_pythonagent(state: ChartGraphState) -> ChartGraphState:
    state["attempts"] = int(state.get("attempts", 0)) + 1
    question = state.get("question", "")
    sql_result = state.get("sql_result", "")
    feedback = state.get("feedback", "")

    print(f"[ChartGraph] pythonagent: 开始生成代码, 尝试次数: {state['attempts']}")

    state["code_raw"] = await python_chart_chain.ainvoke(
        {"question": question, "data": sql_result, "feedback": feedback}
    )
    print(f"[ChartGraph] pythonagent: 代码生成完成, 代码长度: {len(state['code_raw'])}")
    return state


# 节点3: eval
async def _node_eval(state: ChartGraphState) -> ChartGraphState:
    code_raw = state.get("code_raw", "")
    code = _extract_python_code_block(code_raw)

    passed, issues, feedback = _static_eval(code)
    print(f"[ChartGraph] eval: 代码检查通过: {passed}, 问题: {issues}")

    state["eval_pass"] = passed
    state["eval_issues"] = issues
    state["feedback"] = feedback

    if passed:
        state["code"] = code
    return state


# 节点4: pyecharts-sandbox
async def _node_pyecharts_sandbox(state: ChartGraphState) -> ChartGraphState:
    state.pop("chart_html", None)
    state.pop("error", None)

    code = state.get("code", "")
    session_id = state.get("session_id", "")
    user_name = state.get("user_name", "")
    question = state.get("question", "")
    sql_result = state.get("sql_result", "")

    print(f"[ChartGraph] pyecharts_sandbox: 开始执行 Docker 沙箱, 代码长度: {len(code)}")

    try:
        client = docker.from_env()
        container = client.containers.run(
            "pyecharts-sandbox",
            command=["python", "-c", code],
            mem_limit="256m",
            network_disabled=True,
            read_only=True,
            detach=True,
            stdout=True,
            stderr=True,
        )

        result = container.wait()
        stdout = container.logs(stdout=True).decode()
        stderr = container.logs(stderr=True).decode()
        container.remove()

        if result.get("StatusCode", 1) != 0:
            raise RuntimeError(f"Docker execution failed: {stderr}")

        match = re.search(r"CHART_HTML_START(.*?)CHART_HTML_END", stdout, re.DOTALL)
        if not match:
            raise ValueError("沙箱执行成功但未找到 CHART_HTML 标记")

        chart_html = match.group(1)

        chart_html = f"""<!DOCTYPE html>
<html><head><meta charset=\"utf-8\">
<script src=\"http://localhost:3000/js/echarts.js\"><\/script>
<style>
html,body{{margin:0;padding:0;width:100%;height:100%;}}
div[_echarts_instance_]{{width:100%!important;height:100%!important;}}
<\/style>
</head><body>{chart_html}<script>
var charts=document.querySelectorAll('div[_echarts_instance_]');
charts.forEach(function(c){{echarts.init(c).resize();}});
window.onresize=function(){{charts.forEach(function(c){{echarts.getInstanceByDom(c).resize();}});}};
<\/script></body></html>"""

        state["chart_html"] = chart_html
        log_chart_generation(session_id, user_name, question, sql_result, code, True)

    except Exception as e:
        state["error"] = str(e)
        state["feedback"] = (
            "沙箱执行失败，请修改代码并重新输出完整代码。\n"
            f"错误: {e}\n\n"
            "提醒: 只能使用允许的库，并打印 CHART_HTML_START...CHART_HTML_END 标记。"
        )
        log_chart_generation(session_id, user_name, question, sql_result, code, False, str(e))

    return state


# 路由: eval 之后
def _route_after_eval(state: ChartGraphState):
    if not state.get("eval_pass", False):
        if int(state.get("attempts", 0)) >= 3:
            print(f"[ChartGraph] eval: 达到最大重试次数，结束")
            state["error"] = "代码检查失败且达到最大重试次数"
            return END
        print(f"[ChartGraph] eval: 代码检查失败，返回 pythonagent 重试")
        return "pythonagent"
    print(f"[ChartGraph] eval: 代码检查通过，前往 sandbox 执行")
    return "pyecharts_sandbox"


# 路由: sandbox 之后
def _route_after_sandbox(state: ChartGraphState):
    if state.get("chart_html"):
        print(f"[ChartGraph] sandbox: 执行成功，结束")
        return END
    if state.get("error"):
        print(f"[ChartGraph] sandbox: 执行失败，错误: {state['error']}")
        if int(state.get("attempts", 0)) >= 3:
            return END
        return "pythonagent"
    state["error"] = "未知的图表图状态"
    print(f"[ChartGraph] sandbox: 未知状态")
    return END


# 构建工作流
def _build_chart_graph():
    graph = StateGraph(ChartGraphState)

    # 节点
    graph.add_node("sqlagent", _node_sqlagent)
    graph.add_node("pythonagent", _node_pythonagent)
    graph.add_node("eval", _node_eval)
    graph.add_node("pyecharts_sandbox", _node_pyecharts_sandbox)

    # 边
    graph.set_entry_point("sqlagent")
    graph.add_edge("sqlagent", "pythonagent")
    graph.add_edge("pythonagent", "eval")
    graph.add_conditional_edges("eval", _route_after_eval)
    graph.add_conditional_edges("pyecharts_sandbox", _route_after_sandbox)

    return graph.compile()


# 编译一次并复用
chart_graph = _build_chart_graph()
