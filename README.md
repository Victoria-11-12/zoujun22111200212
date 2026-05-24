# LLM Agent 电影数据分析平台

> LangChain/LangGraph 与微服务架构的智能数据分析与可视化系统

> 本项目为 2026 届本科毕业设计，已部署至海外服务器并对外开放。系统采用微服务三后端架构（Node.js + Flask + FastAPI），通过 Nginx 统一代理实现生产级部署，集成 LangGraph 状态机工作流、多层 LLM 安全防御体系、Docker 沙箱隔离等机制，并配套 LangSmith 调用追踪与 Prometheus + Grafana 监控，具备完整的可观测性与运维能力。

## 在线体验

- http://www.movie.victoria1112.cn/demo.html
- 账号：user1  密码：123456

> 若需管理员账号请联系我的指导老师——杨月红老师
> 若您为面试官，我的简历上会附带账密

## 视频演示

- 演示视频：[待录制]()
- 部署视频：[待录制]()

## 核心亮点

- **SQL Agent 性能优化**：通过表结构预注入、工具集精简、推理轮次限制，将 LLM 调用从 6 次降至 1-2 次，响应时间从 30-40 秒优化至 10-15 秒
- **多层 LLM 安全防御**：意图路由分流、正则拦截、Prompt 约束、字段保护、Docker 沙箱、数据库权限隔离，纵深防御注入与越权攻击
- **全链路可观测性**：LangSmith 追踪 LLM 调用链路（token 消耗、延迟、重试），Prometheus + Grafana 监控服务指标（QPS、响应时间、错误率）
- **LangGraph 状态机工作流**：4 节点有向图（SQL 查询 → 代码生成 → 静态检查 → Docker 沙箱执行），支持条件路由与 3 次容错重试，代码在隔离容器中运行，防止恶意代码逃逸
- **Nginx 反向代理**：统一入口，负载均衡，静态资源缓存，解决跨域与端口管理问题
- **LLM-as-Judge 质量评估**：deepseek-v4 评估对话与代码质量，评分 ≥4 数据自动导出 JSONL 用于微调闭环
- **浏览器自动化工具集成**：agent-browser（CLI工具） 封装为 LangChain Tool，本地数据库无结果时自动从百度百科搜索电影信息


## 快速开始

- **[本地开发](./配置文档/guides/INSTALLATION.md)** - 环境搭建与手动启动服务
- **[Docker 部署](./配置文档/deployment/DOCKER.md)** - 一键容器化部署

## 注意事项


### 浏览器搜索功能限制

Docker 部署环境下未打包 Chrome 浏览器（内存占用过大），因此 `agent-browser` 浏览器自动化工具在容器内无法正常工作，百度百科搜索功能不可用。该功能的完整使用需要在宿主机自行安装 Chrome 浏览器后运行。

### 可观测性组件未打包

Docker 部署仅打包项目核心服务，Prometheus 与 Grafana 因内存占用过大未纳入容器。如需体验完整的可观测性监控能力，需自行构建 Prometheus + Grafana 环境并配置数据源接入。

### 首次访问加载

后端服务部署在海外服务器，国内用户首次访问需加载约 875KB 的电影数据（已启用 Gzip 压缩）。受国际链路延迟与 TCP 拥塞控制影响，加载速度因人而异，电信/联通等不同运营商线路体验存在差异。首次加载完成后浏览器缓存数据，后续访问恢复正常。
午高峰和晚高峰掉包率较高，测试时 30s 内能正常出数据，超时请刷新页面重试或更换时间访问，若仍无法加载数据可在 Issues 反馈。


### 测试环境

本项目测试环境与开发环境隔离，如需体验测试需自行构建测试环境或修改配置文件切换到本地环境测试，具体参考 [测试环境配置](./fastapi/测试文档/测试环境配置.md)。

## 系统架构图

![系统架构图](./assets/images/系统架构图.png)

> 更多架构图见各服务文件夹内的 `相关流程图` 目录（Flask、Web\_Node、fastapi）。

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

### 9、LangSmith 调用追踪

![LangSmith追踪](./assets/images/LangSmith追踪.png)

### 10、Grafana 监控仪表盘

![Grafana监控仪表盘](./assets/images/Grafana监控仪表盘.png)

## 技术路线

- 前端使用原生 `JavaScript` + `ECharts`
- 后端使用 `Node.js`、`Flask`、`FastAPI`
- AI 框架使用 `LangChain`、`LangGraph`
- 数据库使用 `MySQL`
- 机器学习使用 `LightGBM`、`Random Forest`
- 运维使用 `Nginx`、`Prometheus`、`Grafana`、`LangSmith`

## 测试

采用经典测试金字塔模型，自底向上分为三层：单元测试（96例）、集成测试（70例）、端到端测试（20例），代码覆盖率 **89%**。

### 单元测试报告

![单元测试报告](./assets/images/测试_单元测试.png)

### 集成测试报告

![集成测试报告](./assets/images/测试_集成测试.png)

### 端到端测试报告

![端到端测试报告](./assets/images/测试_端到端测试.png)

### 详细测试报告

[测试报告](./assets/文档/测试文档/测试报告)

## 详细文档

- [配置文档](./配置文档/README.md) - 配置文档入口与快速导航
- [安装指南](./配置文档/guides/INSTALLATION.md) - 完整的环境搭建教程
- [配置说明](./配置文档/guides/CONFIGURATION.md) - 环境变量与参数配置
- [Docker 部署](./配置文档/deployment/DOCKER.md) - 容器化部署指南
- [监控部署](./配置文档/monitoring/README.md) - Prometheus + Grafana 可观测性部署（可选）
- [常见问题](./配置文档/guides/TROUBLESHOOTING.md) - 问题排查与解决方案
- [更新日志](./更新日志/) - 版本更新记录
- [测试文档](./fastapi/测试文档) - 测试策略与测试报告

