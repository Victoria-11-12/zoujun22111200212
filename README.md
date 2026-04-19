# LLM Agent 数据分析平台 | LangGraph 状态机工作流

> 基于 LangGraph 状态机与微服务架构的智能数据分析系统，集成 LLM 安全防御、LLM-as-Judge 质量评估与 Docker 沙箱隔离。


[![Demo](https://img.shields.io/badge/Demo-Bilibili-blue)](你的 B 站链接)
[![License](https://img.shields.io/badge/License-ISC-green)](LICENSE)

---

## 系统架构

### 微服务三后端架构

| 服务 | 端口 | 技术栈 | 核心职责 |
|------|------|--------|----------|
| Node.js | 3000 | Express 5.x | 用户认证、JWT 签发、RESTful 数据接口、操作日志 |
| Flask | 5000 | Flask + LightGBM/RandomForest | 票房预测、黑马推荐、ROI 可视化 |
| FastAPI | 8000 | FastAPI + LangChain/LangGraph | 用户 SQL Agent、管理员 Agent、LangGraph 绘图工作流、质量评估 |

### FastAPI Agent 架构

![Agent 架构图](docs/images/agent_architecture.png)

---

## 核心功能模块

### 1. LangGraph 绘图工作流（CodeAct 模式）

![绘图流程图](docs/images/chart_workflow.png)

基于 LangGraph 状态机实现自动重试的在线绘图模块：

| 节点 | 功能 | 说明 |
|------|------|------|
| sqlagent | 查询数据 | 调用 SQL Agent 获取绘图数据 |
| pythonagent | 生成代码 | 根据反馈生成 pyecharts 代码 |
| eval | 静态评估 | 检查代码安全性和格式约定 |
| pyecharts_sandbox | Docker 执行 | 沙箱渲染图表 HTML |

**重试机制**：
- 静态评估失败 → 携带 feedback 重试（最多 3 次）
- 沙箱执行失败 → 携带错误信息重试（最多 3 次）

### 2. 用户 SQL Agent（单工具精简架构）

**性能优化**：
- **LLM 调用次数**：从 6 次压缩到 1-2 次（减少 67-83%）
- **响应时间**：从 30-40s 降至 10-15s（提升 2-3 倍）
- **工具数量**：从 4 个精简到 1 个（精简 75%）

**优化策略**：
- 表结构预注入：DDL 直接写入 system prompt
- 精简工具集：只保留 `sql_db_query` 单工具
- 限制推理轮次：`max_iterations` 降为 2

### 3. 管理员 Agent（多工具）

**工具集**：
- `safe_execute_sql`：安全 SQL 执行（含正则检查、自动备份）
- `start_batch`：创建操作批次
- `rollback_batch`：批次回滚
- `create_user`：创建用户（自动加密密码）

### 4. 七层 LLM 安全防御体系

| 层级 | 技术 | 防御内容 |
|:----:|------|----------|
| **第 1 层** | 普通用户意图路由 | 拦截 DELETE/DROP/注入/社会工程攻击 |
| **第 2 层** | 管理员意图路由 | 独立检测，只拦截 DDL/注入 |
| **第 3 层** | Agent Prompt 指令 | 约束 AI 拒绝欺骗手段 |
| **第 4 层** | 正则检查 | 拦截危险关键词（DROP/TRUNCATE/ALTER 等） |
| **第 5 层** | 字段保护 | UPDATE 禁止修改 id/created_at |
| **第 6 层** | Docker 沙箱 | 绘图代码容器化执行 |
| **第 7 层** | 数据库权限隔离 | 普通用户只读，管理员读写 |

### 5. 操作回滚机制

![回滚机制](docs/images/rollback.png)

**备份策略**：
- **DELETE 前**：查询受影响数据，JSON 格式存入 `rollback_logs`
- **UPDATE 前**：查询旧值，存入 `rollback_logs`
- **INSERT 后**：查询新增数据，存入 `rollback_logs`

**回滚工具**：

| 工具 | 功能 |
|------|------|
| `rollback_last` | 撤销最近一次操作 |
| `rollback_batch` | 撤销整个批次（按 batch_id 倒序回滚） |
| `start_batch` | 创建新批次，后续操作归入同一批次 |

### 6. 数据分析师模块（LLM-as-Judge）

![数据分析师模块](docs/images/analyst_module.png)

**四角色权限体系**：

| 角色 | 权限 |
|------|------|
| 游客 | 只读查看数据大屏 |
| 用户 | 查询 movies 表、在线绘图 |
| 数据分析师 | 只读日志表、质量评估、导出 JSONL |
| 管理员 | 增删改查 + 回滚 |

**质量评估流程**：

![质量评估流程](docs/images/eval_flow.png)

**评估维度**：
- 对话评估：相关性、完整性、准确性、格式
- 代码评估：可运行性、图表完整性、工具箱、单位标注、类型匹配

---

## 技术栈

### 核心框架
- **LangGraph** - 状态机工作流引擎（绘图模块 5 节点有向图）
- **LangChain** - LLM Agent 开发框架
- **FastAPI** - 高性能异步 API 服务
- **Flask** - 机器学习模型服务
- **Node.js/Express** - 用户认证与业务接口

### AI 与机器学习
- **DeepSeek V3/R1** - 对话模型与评估模型（LLM-as-Judge）
- **LightGBM/Random Forest** - 票房预测与黑马筛选
- **pyecharts** - 动态图表生成

### 基础设施
- **Docker** - 容器化沙箱隔离
- **MySQL** - 关系型数据库（11 张表）
- **JWT/bcrypt** - 身份认证与加密

> 详细依赖版本见 [requirements.txt](./配置文档/requirements.txt) 和 [package.json](./Web_Node/package.json)

---

**License**: ISC
