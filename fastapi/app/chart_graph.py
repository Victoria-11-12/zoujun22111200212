#==================
#在线图表生成流程
# - 节点: sqlagent -> pythonagent -> eval -> pyecharts-sandbox -> (失败) sandbox-fail-router -> pythonagent
# 结束条件: 沙箱成功返回 chart_html

import re
import docker
from typing import List
from langgraph.graph import StateGraph, END
from app.models import ChartGraphState
from app.sql_agent import sql_executor
from app.chains import python_chart_chain
from app.logs import log_chart_generation


#二、状态机，共享白板，所有节点共享数据，每个节点都可以读写
# ChartGraphState 定义在所有 LangGraph 节点之间传递的共享状态
#（已在 models.py 中定义）

#三、节点三代码评估需要的两个函数
# 1.正则从 markdown 输出中提取 Python 代码块 (```python ... ```)
def _extract_python_code_block(text: str) -> str:
    # 首先尝试查找带标记的 Python 代码块
    match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
    # 如果找到，只使用代码块内容
    if match:
        return match.group(1).strip()
    # 否则，回退到完整文本
    return text.strip()


# 2.静态评估: 仅检查代码是否安全并遵循输出约定
def _static_eval(code: str) -> tuple[bool, List[str], str]:

    issues: List[str] = []    # 收集问题以提供可操作的反馈

    #安全通信检测
    # 约定: 必须从 chart.render_embed() 赋值 CHART_HTML
    if "CHART_HTML" not in code:
        issues.append("Missing CHART_HTML assignment (must use chart.render_embed())")

    # 约定: 必须打印 START/END 标记以便从 stdout 提取 HTML
    if "CHART_HTML_START" not in code or "CHART_HTML_END" not in code:
        issues.append("Missing CHART_HTML_START/CHART_HTML_END markers (stdout extraction needs them)")

    # 允许导入列表，通常pyecharts就够了，如果需要其他模块，也可以添加，越少越安全
    allowed_imports = {"pyecharts"}

    # 禁止导入列表，包含os、sys、subprocess、socket、requests、urllib、open、eval、exec、__import__等危险模块
    banned_tokens = ["import os","import sys","subprocess","socket","requests","urllib","open(","eval(","exec(","__import__",
    ]

    # 在导入行上强制执行允许列表
    for line in code.splitlines():
        # 处理 `import xxx`，遍历识别到import，识别到之后去allowed_imports中检查是否在允许列表中，不存在就添加issues
        if line.startswith("import "):
            module = line.split()[1].split(".")[0]
            if module not in allowed_imports:
                issues.append(f"Illegal import: {module} (allowed: {sorted(allowed_imports)})")
        # 处理 `from xxx import yyy`，遍历识别到from，识别到之后去allowed_imports中检查是否在允许列表中，不存在就添加issues
        if line.startswith("from "):
            module = line.split()[1].split(".")[0]
            if module not in allowed_imports:
                issues.append(f"Illegal from-import: {module} (allowed: {sorted(allowed_imports)})")

    # 检查禁止列表，遍历识别到禁止列表中的模块，如果存在就添加issues
    for token in banned_tokens:
        if token in code:
            issues.append(f"检测到禁止的令牌: {token}")

    passed = len(issues) == 0  # 前面都没有问题长度自然会为0，=结果为True，不等于则False

    # 如果失败，给出修复要点列表
    feedback = "" 
    if not passed:
        feedback = "请修复以下问题并重新输出完整代码:\n- " + "\n- ".join(issues)

    # 返回决策、问题和反馈
    return passed, issues, feedback

#四、 4个节点的实现

# 节点1: sqlagent (复用现有的 sql_executor)
async def _node_sqlagent(state: ChartGraphState) -> ChartGraphState:
    # 读取用户问题
    question = state.get("question", "")
    print(f"[ChartGraph] sqlagent: 开始查询数据库, 问题: {question}")
    # 通过 SQL agent 查询数据库
    result = await sql_executor.ainvoke({"input": question})
    # 存储查询结果供下游代码生成使用
    state["sql_result"] = result.get("output", "")
    print(f"[ChartGraph] sqlagent: 查询完成, 结果长度: {len(state['sql_result'])}")
    # 返回更新后的状态
    return state


# 节点2: pythonagent (生成 pyecharts)
async def _node_pythonagent(state: ChartGraphState) -> ChartGraphState:
    state["attempts"] = int(state.get("attempts", 0)) + 1  # 每次生成代码时增加尝试次数
    question = state.get("question", "")  # 读取用户问题
    sql_result = state.get("sql_result", "")  # 读取 SQL 查询结果
    feedback = state.get("feedback", "")  # 读取反馈修改代码,第一次时没有就为空

    print(f"[ChartGraph] pythonagent: 开始生成代码, 尝试次数: {state['attempts']}")

    # 使用现有的提示链生成代码
    state["code_raw"] = await python_chart_chain.ainvoke(
        {"question": question, "data": sql_result, "feedback": feedback}
    )
    print(f"[ChartGraph] pythonagent: 代码生成完成, 代码长度: {len(state['code_raw'])}")
    # 返回更新后的状态
    return state


# 节点3: eval (静态检查门控; 失败 -> 返回 pythonagent)
async def _node_eval(state: ChartGraphState) -> ChartGraphState:

    code_raw = state.get("code_raw", "")# 读取原始代码
    code = _extract_python_code_block(code_raw)  # 提取纯净 Python 代码

    passed, issues, feedback = _static_eval(code)    # 静态评估检查
    print(f"[ChartGraph] eval: 代码检查通过: {passed}, 问题: {issues}")

    state["eval_pass"] = passed    # 保存决策
    state["eval_issues"] = issues    # 保存问题
    state["feedback"] = feedback    # 保存反馈

    if passed:              # 仅在通过时保存可执行代码
        state["code"] = code
    # 返回更新后的状态
    return state


# 节点4: pyecharts-sandbox (在 Docker 内执行代码; 结束需要 chart_html)
async def _node_pyecharts_sandbox(state: ChartGraphState) -> ChartGraphState:

    state.pop("chart_html", None)    # 清除旧输出以避免陈旧的成功状态
    state.pop("error", None)    # 清除旧错误以避免陈旧的失败状态

    code = state.get("code", "")    # 读取要执行的代码
    session_id = state.get("session_id", "")    # 读取会话ID用于日志记录
    user_name = state.get("user_name", "")    # 读取用户名用于日志记录
    question = state.get("question", "")    # 读取问题用于日志记录
    sql_result = state.get("sql_result", "")    # 读取 SQL 查询结果用于日志记录

    print(f"[ChartGraph] pyecharts_sandbox: 开始执行 Docker 沙箱, 代码长度: {len(code)}")

    try:
        # 创建 docker 客户端
        client = docker.from_env()
        # 运行沙箱容器 
        container = client.containers.run(
            "pyecharts-sandbox",  # 镜像名称
            command=["python", "-c", code],  # 执行命令：使用 Python 解释器运行代码字符串
            mem_limit="256m",  # 内存限制：最大 256MB，防止内存耗尽攻击
            network_disabled=True,  # 禁用网络：防止容器访问外部网络，增强安全性
            read_only=True,  # 只读文件系统：防止容器写入文件，增强安全性
            detach=True,  # 后台运行：容器在后台执行，不阻塞主线程
            stdout=True,  # 捕获标准输出：用于获取图表 HTML 输出
            stderr=True,  # 捕获标准错误：用于获取错误信息
        )

        result = container.wait()        # 等待完成
        stdout = container.logs(stdout=True).decode()        # 读取 stdout
        stderr = container.logs(stderr=True).decode()        # 读取 stderr
        container.remove()        # 移除容器以避免累积

        # 非零退出码意味着失败
        if result.get("StatusCode", 1) != 0:
            raise RuntimeError(f"Docker execution failed: {stderr}")

        # 从 stdout 提取 CHART_HTML
        match = re.search(r"CHART_HTML_START(.*?)CHART_HTML_END", stdout, re.DOTALL)
        # 缺少标记意味着输出约定被破坏
        if not match:
            raise ValueError("沙箱执行成功但未找到 CHART_HTML 标记")

        # 获取嵌入的 HTML 片段
        chart_html = match.group(1)

        # 保留原始页面嵌入包装器 + echarts.js 链接
        # 将图表 HTML 包装成完整页面，确保正确显示和响应式调整
        chart_html = f"""<!DOCTYPE html>
<html><head><meta charset=\"utf-8\">
<script src=\"http://localhost:3000/js/echarts.js\"><\/script>  <!-- 引入 ECharts 库 -->
<style>
html,body{{margin:0;padding:0;width:100%;height:100%;}}  <!-- 移除默认边距，占满窗口 -->
div[_echarts_instance_]{{width:100%!important;height:100%!important;}}  <!-- 强制图表容器占满 100% -->
<\/style>
</head><body>{chart_html}<script>
var charts=document.querySelectorAll('div[_echarts_instance_]');  <!-- 查找所有图表容器 -->
charts.forEach(function(c){{echarts.init(c).resize();}});  <!-- 初始化并调整图表大小 -->
window.onresize=function(){{charts.forEach(function(c){{echarts.getInstanceByDom(c).resize();}});}};  <!-- 窗口大小改变时响应式调整 -->
<\/script></body></html>"""

        # 保存最终 HTML (结束条件依赖于此)
        state["chart_html"] = chart_html

        # 记录成功
        log_chart_generation(session_id, user_name, question, sql_result, code, True)

    except Exception as e:
        # 保存错误用于路由
        state["error"] = str(e)
        # 将错误翻译为 LLM 可理解的反馈，供 pythonagent 重试时使用
        state["feedback"] = (
            "沙箱执行失败，请修改代码并重新输出完整代码。\n"
            f"错误: {e}\n\n"
            "提醒: 只能使用允许的库，并打印 CHART_HTML_START...CHART_HTML_END 标记。"
        )
        # 记录失败以供后续检查
        log_chart_generation(session_id, user_name, question, sql_result, code, False, str(e))

    # 返回更新后的状态
    return state



#五、 两个路由节点
# 路由: eval 之后，决定下一个节点
def _route_after_eval(state: ChartGraphState):
    # 如果 eval 失败，重试生成 ，最多3次
    if not state.get("eval_pass", False):
        # 如果达到重试限制则停止
        if int(state.get("attempts", 0)) >= 3:
            print(f"[ChartGraph] eval: 达到最大重试次数，结束")
            state["error"] = "代码检查失败且达到最大重试次数"
            return END
        # 否则，返回 pythonagent
        print(f"[ChartGraph] eval: 代码检查失败，返回 pythonagent 重试")
        return "pythonagent"
    # 如果 eval 通过，在沙箱中执行
    print(f"[ChartGraph] eval: 代码检查通过，前往 sandbox 执行")
    return "pyecharts_sandbox"


# 路由: sandbox 之后，决定结束或重试
def _route_after_sandbox(state: ChartGraphState):
    # 成功意味着我们有 chart_html
    if state.get("chart_html"):
        print(f"[ChartGraph] sandbox: 执行成功，结束")
        return END
    # 失败意味着我们有错误
    if state.get("error"):
        print(f"[ChartGraph] sandbox: 执行失败，错误: {state['error']}")
        # 如果达到重试限制则停止
        if int(state.get("attempts", 0)) >= 3:
            return END
        # 跳到节点2重新写代码
        return "pythonagent"
    # 防御性回退，如果既没有 chart_html 也没有 error，返回未知状态
    state["error"] = "未知的图表图状态"
    print(f"[ChartGraph] sandbox: 未知状态")
    return END


#六、 构建工作流
def _build_chart_graph():

    graph = StateGraph(ChartGraphState)    # 创建状态图

    #节点
    graph.add_node("sqlagent", _node_sqlagent)    # 添加 sqlagent 节点
    graph.add_node("pythonagent", _node_pythonagent)    # 添加 pythonagent 节点
    graph.add_node("eval", _node_eval)    # 添加 eval 节点
    graph.add_node("pyecharts_sandbox", _node_pyecharts_sandbox)    # 添加沙箱执行节点
 
    #边
    graph.set_entry_point("sqlagent")    # 设置入口点
    graph.add_edge("sqlagent", "pythonagent")    # 连接 sqlagent -> pythonagent
    graph.add_edge("pythonagent", "eval")    # 连接 pythonagent -> eval
    graph.add_conditional_edges("eval", _route_after_eval)    # eval 之后的条件路由
    graph.add_conditional_edges("pyecharts_sandbox", _route_after_sandbox)    # sandbox 之后的条件路由
 

    # 编译图
    return graph.compile()

# 编译一次并复用
chart_graph = _build_chart_graph()
