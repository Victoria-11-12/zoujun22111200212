# GLM-5.1 测试划分分析报告

## 一、总体评估

测试划分文档整体结构清晰，分层合理，覆盖了项目的主要模块。但存在以下问题：部分测试对象遗漏、少量分类不一致、个别冗余项。以下逐模块详细分析。

---

## 二、数量统计对比

| 测试层级 | 文档中测试项数 | 实际应测试项数 | 差异 |
|---------|-------------|-------------|------|
| 单元测试 | 33 | 42 | +9 |
| 集成测试 | 39 | 38 | -1 |
| E2E测试（端点） | 7 | 7 | 0 |
| E2E测试（场景） | 20 | 20 | 0 |
| **合计** | **79** | **87** | **+8** |

---

## 三、遗漏项详细分析

### 3.1 单元测试遗漏（9项）

#### (1) `app/tools/admin_tools.py` — DANGEROUS_KEYWORDS 常量验证

源码第16行定义了危险关键词正则列表 `DANGEROUS_KEYWORDS`，该常量直接影响 `check_sql_safety` 的行为，应测试其内容完整性和正则有效性。

**遗漏原因**：文档只关注了使用该常量的函数，未关注常量本身。

#### (2) `app/tools/admin_tools.py` — admin_tools 工具列表验证

源码第265行定义了 `admin_tools = [create_user, safe_execute_sql, rollback_batch, start_batch]`，应验证列表包含的工具数量和顺序是否正确，防止工具遗漏或顺序错误影响Agent行为。

**遗漏原因**：文档未关注工具注册列表的完整性。

#### (3) `app/config.py` — MODEL_NAME 常量

源码第53行 `MODEL_NAME = os.getenv('MODEL_NAME')`，该常量被 `logs.py` 中所有日志函数使用，是日志记录的关键字段，应单独验证其正确读取。

**遗漏原因**：文档只列出了需要Mock环境变量的初始化对象，遗漏了此简单但被广泛依赖的常量。

#### (4) `app/config.py` — DOCKER_HOST 环境变量设置

源码第4行 `os.environ['DOCKER_HOST'] = 'npipe:////./pipe/docker_engine'`，这是Windows Docker连接的关键配置，在import时即执行副作用，应测试该值是否正确设置。

**遗漏原因**：文档未关注config.py中的环境变量写入操作。

#### (5) `app/config.py` — DB_URI_ANALYST 变量

源码第66行 `DB_URI_ANALYST = f"mysql+pymysql://..."` ，该URI字符串构造逻辑应被测试，确保环境变量缺失时有合理的错误处理。

**遗漏原因**：文档只列出了 `engine_analyst`，未列出构造它的中间变量。

#### (6) `app/workflows/chart_workflow.py` — _extract_python_code_block 无标记回退逻辑

文档已列出此函数，但测试内容仅写"代码提取正则"，未明确要求测试**无markdown标记时的回退逻辑**（源码第36-37行，当找不到 ```python 标记时回退到完整文本）。这是一个重要的边界条件。

#### (7) `app/workflows/chart_workflow.py` — _static_eval 允许导入列表边界

文档已列出此函数，但测试内容仅写"静态代码检查、安全检测"，未明确要求测试**允许导入列表的边界**（只允许pyecharts，其他如numpy/pandas应被拦截）以及**from-import形式**的检测。

#### (8) `app/workflows/chart_workflow.py` — _route_after_eval 达到最大重试次数的END路由

文档已列出此函数，但测试内容仅写"条件路由逻辑"，未明确要求测试 `attempts >= 3` 时返回END的边界条件。

#### (9) `app/workflows/chart_workflow.py` — _route_after_sandbox 未知状态处理

文档已列出此函数，但测试内容仅写"条件路由逻辑"，未明确要求测试既无chart_html又无error的未知状态分支（源码第216行）。

### 3.2 集成测试遗漏（4项）

#### (1) `app/services/analyst_service.py` — evaluate_records_task_async 函数

源码第129-135行，该函数负责异步并发执行评估任务，使用 `asyncio.Semaphore(5)` 控制并发数，通过 `asyncio.gather` 并行调度。应测试并发控制和任务完成后的状态更新。

**遗漏原因**：文档只列出了 `start_evaluation` 和 `eval_one`，遗漏了中间的异步调度函数。

#### (2) `app/services/analyst_service.py` — eval_progress / eval_lock 全局状态管理

源码第15-16行定义了 `eval_progress` 和 `eval_lock`，这是跨线程共享的状态，应测试并发场景下的状态一致性（如同时启动两个评估任务时第二个应被拒绝）。

**遗漏原因**：文档未将全局并发状态作为独立测试对象。

#### (3) `app/workflows/chart_workflow.py` — _build_chart_graph 图构建逻辑

源码第222-238行，该函数负责构建LangGraph状态图，包括节点注册、边连接、条件路由配置。应测试图的拓扑结构是否正确（节点数量、边的连接关系）。

**遗漏原因**：文档只列出了 `chart_graph` 编译结果，未列出构建过程。

#### (4) `app/workflows/chart_workflow.py` — _node_pyecharts_sandbox HTML模板构造

源码第165-176行，sandbox节点成功执行后会构造一个完整的HTML模板包裹chart_html，包含echarts.js引用、样式、resize脚本。该模板构造逻辑复杂，应独立测试。

**遗漏原因**：文档测试内容仅写"Docker沙箱执行、HTML提取"，未关注HTML模板的构造逻辑。

---

## 四、分类不一致分析

### 4.1 应归入单元测试但放在集成测试中的项

| 测试对象 | 当前分类 | 应有分类 | 原因 |
|---------|---------|---------|------|
| ChartGraphState | 集成测试(2.3) | 单元测试 | TypedDict定义，纯类型声明，无外部依赖 |
| _extract_python_code_block | 集成测试(2.3) | 单元测试 | 纯函数，仅依赖re模块，无外部依赖 |
| _static_eval | 集成测试(2.3) | 单元测试 | 纯函数，仅做字符串检查，无外部依赖 |
| _route_after_eval | 集成测试(2.3) | 单元测试 | 纯函数，仅读取dict字段做条件判断 |
| _route_after_sandbox | 集成测试(2.3) | 单元测试 | 纯函数，仅读取dict字段做条件判断 |
| get_progress (analyst_service) | 集成测试(2.4) | 单元测试 | 仅返回全局dict的copy，无外部依赖 |

**说明**：文档第四章"测试分层总结"的4.1节已正确将前5项归入"纯单元测试"，但正文表格中仍放在集成测试章节，存在前后不一致。`get_progress` 在4.1节也被标注为单元测试，但正文放在2.4集成测试中。

### 4.2 建议调整

将上述6项从集成测试章节移至单元测试章节，使文档结构自洽。调整后数量变化：

| 测试层级 | 调整前 | 调整后 |
|---------|-------|-------|
| 单元测试 | 33 | 39 |
| 集成测试 | 39 | 33 |

---

## 五、冗余项分析

### 5.1 config.py 全部7项作为单元测试的价值有限

`llm`、`db`、`db_user`、`engine`、`engine_readonly`、`eval_llm`、`engine_analyst` 均为模块级初始化对象，在import时即执行。将它们作为单元测试逐个Mock环境变量测试，实际验证的只是"环境变量能正确传入构造函数"，价值有限。

**建议**：保留但降低优先级，合并为1-2个测试（如"配置模块加载测试"和"连接池参数测试"），而非7个独立测试项。

### 5.2 E2E测试场景存在潜在重叠

- 用户对话"安全威胁请求→警告拦截"与管理员对话"安全威胁请求→警告拦截"场景高度相似
- 图表"安全代码检测→危险代码拦截"与用户"安全威胁请求"在意图路由层有重叠

**建议**：E2E层保留这些场景（因为端点不同），但在集成测试层避免重复测试相同的安全拦截逻辑。

---

## 六、测试内容细化不足分析

以下测试对象的测试内容描述过于笼统，缺少关键边界条件：

| 测试对象 | 文档描述 | 缺失的边界条件 |
|---------|---------|-------------|
| check_sql_safety | 危险关键词检测、正则匹配 | 注释符`--`在SQL中间位置的检测；分号后跟关键字`;\s*\w`的匹配；大小写混合绕过尝试 |
| save_history | 消息追加、历史截断、LangChain消息封装 | 截断时机精确验证（恰好等于MAX_HISTORY*2时不截断，超过1条时截断）；空字符串消息处理 |
| safe_execute_sql | SQL执行、安全拦截、备份触发 | SELECT查询结果为空时的返回值；UPDATE/DELETE无WHERE子句时的行为；表名/条件正则匹配失败时的行为 |
| rollback_batch | 回滚逻辑、数据恢复 | 无可回滚记录时的返回；批次内混合INSERT/UPDATE/DELETE操作的回滚顺序；回滚日志清理验证 |
| _static_eval | 静态代码检查、安全检测 | `from pyecharts.xxx import yyy`形式的检测；banned_tokens部分匹配问题（如`eval(`出现在字符串中） |
| start_evaluation | 批量评估任务启动、进度管理 | 已有任务运行时再次启动的拒绝逻辑；空记录集的处理；日期过滤参数的SQL注入防护 |

---

## 七、各模块测试覆盖评分

| 模块 | 文档覆盖项 | 实际应测项 | 覆盖率 | 评级 |
|-----|----------|----------|-------|------|
| models.py | 7 | 7 | 100% | A |
| history.py | 4 | 4 | 100% | A |
| logs.py | 5 | 5 | 100% | A |
| config.py | 7 | 9 | 78% | B |
| sql_tools.py | 1 | 1 | 100% | A |
| admin_tools.py | 7 | 9 | 78% | B |
| web_tools.py | 2 | 2 | 100% | A |
| user_chains.py | 4 | 4 | 100% | A |
| admin_chains.py | 2 | 2 | 100% | A |
| chart_chains.py | 3 | 3 | 100% | A |
| eval_chains.py | 2 | 2 | 100% | A |
| sql_agent.py | 2 | 3 | 67% | C |
| admin_agent.py | 2 | 2 | 100% | A |
| chart_workflow.py | 10 | 12 | 83% | B |
| user_service.py | 4 | 4 | 100% | A |
| admin_service.py | 2 | 2 | 100% | A |
| chart_service.py | 1 | 1 | 100% | A |
| analyst_service.py | 7 | 9 | 78% | B |
| routers (全部) | 7 | 7 | 100% | A |

**整体覆盖率：79/87 = 90.8%**

---

## 八、总结

### 8.1 主要问题

1. **遗漏8个测试项**：集中在config.py常量/环境变量、admin_tools常量/列表、analyst_service异步函数/并发状态、chart_workflow构建逻辑/HTML模板
2. **分类不一致**：6个纯函数被错误归入集成测试，文档第四章与正文矛盾
3. **测试内容描述笼统**：多个关键函数缺少边界条件描述，可能导致测试用例不够充分
4. **config.py测试冗余**：7个初始化对象的单元测试价值有限，建议合并

### 8.2 优点

1. 三层测试分层（单元/集成/E2E）结构清晰
2. 测试依赖矩阵完整，Mock需求标注明确
3. 优先级划分合理，P0核心功能覆盖到位
4. E2E场景覆盖全面，包含正常/异常/安全场景

### 8.3 修正后的数量统计

| 测试层级 | 文档原数量 | 修正后数量 | 变化 |
|---------|----------|----------|------|
| 单元测试 | 33 | 42 | +9（补充遗漏+分类调整） |
| 集成测试 | 39 | 33 | -6（分类调整） |
| E2E测试 | 7端点/20场景 | 7端点/20场景 | 不变 |
| **合计** | **79** | **82项+20场景** | — |
