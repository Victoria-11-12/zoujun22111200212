# 项目配置文档

本文档包含 LLM Agent 数据分析平台的完整配置说明。

## 文档结构

```
配置文档/
├── README.md                 # 本文档 - 配置文档入口
├── .env.example              # 环境变量模板
├── requirements.txt          # Python 依赖列表
├── movie_db.sql              # 数据库初始化脚本
├── guides/                   # 使用指南
│   ├── INSTALLATION.md       # 安装指南
│   ├── CONFIGURATION.md      # 配置说明
│   └── TROUBLESHOOTING.md    # 常见问题
├── deployment/               # 部署文档
│   ├── DOCKER.md             # Docker 部署指南
│   └── docker-compose.yml    # Docker Compose 配置
├── docker/                   # Dockerfile 目录
│   ├── Dockerfile.fastapi    # FastAPI 服务
│   ├── Dockerfile.flask      # Flask 服务
│   └── Dockerfile.nodejs     # Node.js 服务
├── nginx/                    # Nginx 配置
│   ├── nginx.conf            # 生产环境配置
│   └── nginx.local.conf      # 本地开发配置
└── monitoring/               # 可观测性监控（可选）
    ├── README.md             # 监控部署指南
    ├── docker-compose.monitoring.yml  # 监控组件 Compose 配置
    └── prometheus.yml        # Prometheus 抓取配置
```

## 快速开始

### 1. 环境要求

| 软件 | 版本要求 | 用途 |
|------|---------|------|
| Python | 3.10+ | FastAPI 和 Flask 服务 |
| Node.js | 16+ | 前端服务和认证服务 |
| MySQL | 5.7+ / 8.0+ | 数据存储 |
| Docker | 20.10+ | 沙箱隔离（可选） |

### 2. 快速启动

```bash
# 1. 导入数据库
mysql -u root -p < movie_db.sql

# 2. 配置环境变量
cp .env.example ../fastapi/.env
# 编辑 .env 填写实际配置

# 3. 安装依赖
pip install -r requirements.txt
cd ../Web_Node && npm install

# 4. 启动服务
# 终端1: Node.js
cd Web_Node && node app.js
# 终端2: Flask
cd Flask && python app2.py
# 终端3: FastAPI
cd fastapi && uvicorn app3:app --reload
```

### 3. Docker 部署

```bash
cd 配置文档/deployment
docker-compose up -d
```

## 详细文档

- [安装指南](./guides/INSTALLATION.md) - 完整的环境搭建步骤
- [配置说明](./guides/CONFIGURATION.md) - 环境变量与参数配置
- [Docker 部署](./deployment/DOCKER.md) - 容器化部署指南
- [监控部署](./monitoring/README.md) - Prometheus + Grafana 可观测性部署（可选）
- [常见问题](./guides/TROUBLESHOOTING.md) - 问题排查与解决方案

## 配置文件说明

| 文件 | 说明 |
|------|------|
| `.env.example` | 环境变量模板，复制到 `fastapi/.env` 后填写实际值 |
| `requirements.txt` | Python 依赖列表，用于安装 FastAPI/Flask 依赖 |
| `movie_db.sql` | 数据库结构和初始数据 |
| `docker-compose.yml` | Docker Compose 部署配置 |

## 技术支持

如有问题，请参考：
1. [项目 README](../README.md)
2. [更新日志](../更新日志/)
3. FastAPI API 文档：启动后访问 http://localhost:8000/docs
