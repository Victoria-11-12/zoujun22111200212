# LLM Agent 数据分析平台

> LangChain/LangGraph 与微服务架构的智能数据分析与可视化系统

> 本项目为 2026 届本科毕业设计，构建了一套生产级的 LLM Agent 数据分析平台。系统采用微服务三后端架构，集成自然语言查询、AI 自动绘图、票房预测、质量评估等核心能力，并设计了多层 LLM 安全防御体系，解决大模型应用在生产环境的可控性与安全性问题。

## 视频演示

- 演示视频：[待补充]()
- 部署视频：[待补充]()

## 核心亮点

- **SQL Agent 性能优化**：通过表结构预注入、工具集精简、推理轮次限制，将 LLM 调用从 6 次降至 1-2 次，响应时间从 30-40 秒优化至 10-15 秒
- **LangGraph 状态机工作流**：4 节点有向图（SQL 查询 → 代码生成 → 静态检查 → Docker 沙箱执行），支持条件路由与 3 次容错重试
- **多层 LLM 安全防御**：意图路由分流、正则拦截、Prompt 约束、字段保护、Docker 沙箱、数据库权限隔离，纵深防御注入与越权攻击
- **LLM-as-Judge 质量评估**：deepseek-v4评估对话与代码质量，评分 ≥4 数据自动导出 JSONL 用于微调闭环
- **微服务三后端**：Node.js（业务）+ Flask（算法）+ FastAPI（Agent），独立部署，支持水平扩展
- **操作回滚机制**：管理员 DELETE/UPDATE/INSERT 操作自动备份，支持批次级误操作恢复
- **浏览器自动化工具集成**：agent-browser（CLI工具） 封装为 LangChain Tool，本地数据库无结果时自动从百度百科搜索电影信息


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
- [x] 百度百科搜索工具集成（agent-browser）

## 快速开始

- **[本地开发](./配置文档/guides/INSTALLATION.md)** - 环境搭建与手动启动服务
- **[Docker 部署](./配置文档/deployment/DOCKER.md)** - 一键容器化部署

## 注意事项

### 访问方式

本站为毕业设计展示用途，仅供面试官体验，不对公众开放。访问地址及管理员账号已随简历附上，恕不另行公开。

### 浏览器搜索功能限制

Docker 部署环境下未打包 Chrome 浏览器（内存占用过大），因此 `agent-browser` 浏览器自动化工具在容器内无法正常工作，百度百科搜索功能不可用。该功能的完整使用需要在宿主机自行安装 Chrome 浏览器后运行。

### 首次访问冷启动

后端服务部署在海外服务器，由于服务启动后空闲连接会被回收，首次访问或长时间未操作后重新使用，需要等待约 10 秒的冷启动时间，后续请求恢复正常响应速度。

### 网络延迟

数据库服务器与应用服务器之间存在地理位置距离，实际访问速度较本地测试环境稍慢，属于正常现象。

### 测试环境

本项目测试环境与生产环境隔离，如需体验测试需自行构建测试环境或修改配置文件切换到本地环境测试，具体参考 [测试环境配置](./fastapi/测试文档/测试环境配置.md)。

## 项目截图

### 1、可视化大屏

![可视化大屏](./assets/images/可视化大屏.png)

### 2、管理员界面

![管理员界面](./assets/images/管理员界面.png)

### 3、票房预测

![票房预测](./assets/images/票房预测.png)

### 4、用户 AI 对话

![用户AI对话1](./assets/images/用户AI对话1.png)

![用户AI对话2](./assets/images/用户AI对话2.png)

### 5、管理员 AI 对话

![管理员AI1](./assets/images/管理员AI1.png)

![管理员AI2](./assets/images/管理员AI2.png)

### 6、在线绘图

![在线绘图1](./assets/images/在线绘图1.png)

![在线绘图2](./assets/images/在线绘图2.png)

### 7、数据分析师

![LLM-as-a-Judge](./assets/images/LLM-as-a-Judge.png)

![导出json](./assets/images/导出json.png)

### 8、SQL 注入拦截

![SQL注入](./assets/images/SQL注入.png)

## 系统架构图

![系统架构图](./assets/images/系统架构图.png)

> 更多架构图见各服务文件夹内的 `相关流程图` 目录（Flask、Web\_Node、fastapi）。
> Nginx为后续引入，项目流程流程图里暂无Nginx反向代理

## 技术路线

- 前端使用 `HTML`、`CSS`、`JavaScript`、`ECharts`
- 后端使用 `Node.js`、`Flask`、`FastAPI`
- AI 框架使用 `LangChain`、`LangGraph`
- 数据库使用 `MySQL`
- 机器学习使用 `LightGBM`、`Random Forest`

## 测试

采用经典测试金字塔模型，自底向上分为三层：单元测试（96例）、集成测试（70例）、端到端测试（20例），代码覆盖率 **89%**。

### 单元测试报告

![单元测试报告](./assets/images/测试_单元测试.png)

### 集成测试报告

![集成测试报告](./assets/images/测试_集成测试.png)

### 端到端测试报告

![端到端测试报告](./assets/images/测试_端到端测试.png)

### 详细测试报告

[测试报告](./fastapi/测试文档/测试报告)

## 详细文档

- [配置文档](./配置文档/README.md) - 配置文档入口与快速导航
- [安装指南](./配置文档/guides/INSTALLATION.md) - 完整的环境搭建教程
- [配置说明](./配置文档/guides/CONFIGURATION.md) - 环境变量与参数配置
- [Docker 部署](./配置文档/deployment/DOCKER.md) - 容器化部署指南
- [常见问题](./配置文档/guides/TROUBLESHOOTING.md) - 问题排查与解决方案
- [更新日志](./更新日志/) - 版本更新记录
- [测试文档](./fastapi/测试文档) - 测试策略等详细文档

