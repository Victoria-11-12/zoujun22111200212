# LLM Agent 数据分析平台
>LangChain/LangGraph 与微服务架构的智能数据分析与可视化系统

> 本项目为 2026 届本科毕业设计，构建了一套生产级的 LLM Agent 数据分析平台。系统采用微服务三后端架构，集成自然语言查询、AI 自动绘图、票房预测、质量评估等核心能力，并设计了多层 LLM 安全防御体系，解决大模型应用在生产环境的可控性与安全性问题。

## 核心亮点

- **LangGraph 状态机工作流**：4 节点有向图（SQL 查询 → 代码生成 → 静态检查 → Docker 沙箱执行），支持条件路由与 3 次容错重试
- **多层 LLM 安全防御**：意图路由分流、正则拦截、Prompt 约束、字段保护、Docker 沙箱、数据库权限隔离，纵深防御注入与越权攻击
- **LLM-as-Judge 质量评估**：DeepSeek-R1 评估对话与代码质量，评分 ≥4 数据自动导出 JSONL 用于微调闭环
- **微服务三后端**：Node.js（认证）+ Flask（算法）+ FastAPI（Agent），独立部署，支持水平扩展
- **操作回滚机制**：管理员 DELETE/UPDATE/INSERT 操作自动备份，支持批次级误操作恢复

## LLM 安全架构


系统采用三层防御路径：

| 路径 | 防御措施 |
|------|----------|
| **普通用户** | 意图识别 → SQL Agent → 只读数据库连接 → 拦截危险词 → 提示词约束（禁止DDL/全表扫描/LIMIT） |
| **管理员** | 意图路由 → 危险词检测（DROP/ALTER/--/#） → safe_execute_sql → 正则安全检查 → 操作前自动备份 → 执行 |
| **图表生成** | 静态代码检查 → 白名单导入（仅pyecharts） → 禁止危险令牌（os/sys/eval） → Docker沙箱执行 → 禁用网络/只读/内存限制 |

所有操作统一记录安全日志，异常请求直接拦截并返回警告。

## 功能

- [x] 用户登录注册
- [x] AI 对话查询（SQL Agent）
- [x] 在线绘图（LangGraph 工作流）
- [x] 票房预测（LightGBM/随机森林）
- [x] 黑马电影推荐
- [x] 数据大屏可视化
- [x] 管理员后台
- [x] 操作回滚机制
- [x] LLM 安全防御（多层）
- [x] LLM-as-Judge 质量评估
- [x] Docker 沙箱隔离

## 快速开始

详细配置和启动步骤请查看 **[配置文档](./配置文档/CONFIG.md)**。

## 项目截图

### 1、可视化大屏

![可视化大屏](./document/screenshots/可视化大屏.png)

### 2、管理员界面

![管理员界面](./document/screenshots/管理员界面.png)

### 3、票房预测

![票房预测](./document/screenshots/票房预测.png)

### 4、用户 AI 对话

![用户AI对话1](./document/screenshots/用户AI对话1.png)

![用户AI对话2](./document/screenshots/用户AI对话2.png)

### 5、管理员 AI 对话

![管理员AI1](./document/screenshots/管理员AI1.png)

![管理员AI2](./document/screenshots/管理员AI2.png)

### 6、在线绘图

![在线绘图1](./document/screenshots/在线绘图1.png)

![在线绘图2](./document/screenshots/在线绘图2.png)

### 7、数据分析师

![LLM-as-a-Judge](./document/screenshots/LLM-as-a-Judge.png)

![导出json](./document/screenshots/导出json.png)

### 8、SQL 注入拦截

![SQL注入](./document/screenshots/SQL注入.png)

## 系统架构图

![系统架构图](./document/screenshots/系统架构图.png)

> 更多架构图见各服务文件夹内的 `相关流程图` 目录（Flask、Web_Node、fastapi）。

## 技术路线

- 前端使用 `HTML`、`CSS`、`JavaScript`、`ECharts`
- 后端使用 `Node.js`、`Flask`、`FastAPI`
- AI 框架使用 `LangChain`、`LangGraph`
- 数据库使用 `MySQL`
- 机器学习使用 `LightGBM`、`Random Forest`

## 详细文档

- [配置文档](./配置文档/CONFIG.md) - 完整的环境配置说明
- [更新日志](./更新日志/) - 版本更新记录
