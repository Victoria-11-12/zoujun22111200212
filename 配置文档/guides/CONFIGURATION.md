# 配置说明

本文档详细说明项目的环境变量和参数配置。

## 目录

- [环境变量配置](#环境变量配置)
- [数据库配置](#数据库配置)
- [LLM API 配置](#llm-api-配置)
- [JWT 配置](#jwt-配置)
- [Docker 配置](#docker-配置)

---

## 环境变量配置

### 1. 创建 .env 文件

```bash
# 复制模板文件
cp .env.example ../fastapi/.env

# 编辑配置文件
# Windows:
notepad ../fastapi/.env
# macOS/Linux:
nano ../fastapi/.env
```

---

## 数据库配置

### 必填配置项

```env
# MySQL 数据库主机地址
DB_HOST=localhost

# 数据库名称
DB_NAME=movie_db

# 管理员数据库用户名（读写权限，用于 FastAPI 和 Node.js）
DB_USER=root

# 管理员数据库密码
DB_PASS=your_mysql_password

# 只读数据库用户名（普通用户使用，用于 FastAPI、Flask）
DB_USER_READONLY=readonly_user

# 只读数据库密码
DB_PASS_READONLY=your_readonly_password

# 分析师数据库用户（用于评估模块查询日志表和写入评估结果表）
DB_USER_ANALYST=analyst

# 分析师数据库密码
DB_PASS_ANALYST=your_analyst_password
```

### 数据库表说明

| 表名 | 说明 | 权限要求 |
|------|------|---------|
| `movies` | 电影数据（~8000条） | 只读/读写 |
| `users` | 用户信息 | 读写 |
| `logs` | 操作日志 | 读写 |
| `user_chat_logs` | 用户对话日志 | 读写 |
| `admin_chat_logs` | 管理员对话日志 | 读写 |
| `security_warning_logs` | 安全警告日志 | 读写 |
| `user_messages` | 用户留言 | 读写 |
| `rollback_logs` | 操作回滚日志 | 读写 |
| `chart_configs` | 图表配置 | 读写 |
| `chart_generation_logs` | 图表生成日志 | 读写 |
| `eval_results` | 评估结果 | 读写 |

---

## LLM API 配置

### 必填配置项

```env
# API 基础地址（支持 OpenAI 兼容的 API）
# DeepSeek: https://api.deepseek.com/v1
# OpenAI: https://api.openai.com/v1
API_BASE=https://api.deepseek.com/v1

# API 密钥
API_KEY=your_deepseek_api_key

# 对话模型名称
# DeepSeek: deepseek-v4-flash, deepseek-chat 等
# OpenAI: gpt-4, gpt-3.5-turbo
MODEL_NAME=deepseek-v4-flash
```

### 获取 DeepSeek API Key

1. 访问 [DeepSeek 官网](https://www.deepseek.com/)
2. 注册账号并登录
3. 进入 [API Keys 页面](https://platform.deepseek.com/api_keys)
4. 点击 "创建 API Key"
5. 复制 API Key 并填入 `.env` 文件

**费用说明:**
- DeepSeek Chat: ¥1/百万 tokens（输入），¥2/百万 tokens（输出）
- 新用户赠送 ¥10 体验金

### 评估模型配置（可选）

```env
# 评估 API 密钥（可与上面 API_KEY 相同）
EVAL_API_KEY=your_eval_api_key

# 评估模型名称
# DeepSeek: deepseek-v4-flash, deepseek-reasoner 等
# OpenAI: gpt-4
EVAL_MODEL_NAME=deepseek-v4-flash
```

---

## JWT 配置

### Node.js 服务配置

```env
# JWT 密钥（请使用随机字符串）
JWT_SECRET=your_random_secret_string

# JWT 过期时间（单位：小时，默认24小时）
JWT_EXPIRES_IN=24
```

---

## Docker 配置

### 服务端口配置

```env
# Node.js 服务端口
NODE_PORT=3000

# Flask 服务端口
FLASK_PORT=5000

# FastAPI 服务端口
FASTAPI_PORT=8000
```

### CodeAct Agent 沙箱配置

```env
# Docker 镜像名称（用于 pyecharts 绘图沙箱）
DOCKER_IMAGE=pyecharts-sandbox

# Docker 内存限制（单位：MB）
DOCKER_MEMORY_LIMIT=256

# Docker 执行超时时间（单位：秒）
DOCKER_TIMEOUT=30
```

### 安全配置

CodeAct Agent 在 Docker 容器中执行代码时，会应用以下安全限制：

| 限制项 | 配置 | 说明 |
|--------|------|------|
| 网络禁用 | `network_disabled=True` | 容器无法访问外部网络 |
| 内存限制 | `mem_limit='256m'` | 限制内存使用 |
| 执行超时 | `timeout=30` | 30秒超时 |
| 只读文件系统 | `read_only=True` | 禁止写入文件 |

---

## 完整配置示例

```env
# ========================================
# 数据库配置
# ========================================
DB_HOST=localhost
DB_NAME=movie_db
DB_USER=root
DB_PASS=your_password
DB_USER_READONLY=readonly_user
DB_PASS_READONLY=readonly_password
DB_USER_ANALYST=analyst
DB_PASS_ANALYST=your_analyst_password

# ========================================
# LLM API 配置
# ========================================
API_BASE=https://api.deepseek.com/v1
API_KEY=your_api_key_here
MODEL_NAME=deepseek-v4-flash

# ========================================
# 评估模型配置
# ========================================
EVAL_API_KEY=your_eval_api_key_here
EVAL_MODEL_NAME=deepseek-v4-flash

# ========================================
# JWT 配置
# ========================================
JWT_SECRET=your_jwt_secret_key_here
JWT_EXPIRES_IN=24

# ========================================
# 服务端口配置
# ========================================
NODE_PORT=3000
FLASK_PORT=5000
FASTAPI_PORT=8000

# ========================================
# Docker 配置
# ========================================
DOCKER_IMAGE=pyecharts-sandbox
DOCKER_MEMORY_LIMIT=256
DOCKER_TIMEOUT=30
```

---

## 配置文件清单

| 文件 | 位置 | 说明 |
|------|------|------|
| `.env.example` | 配置文档/ | 环境变量模板 |
| `requirements.txt` | 配置文档/ | Python 依赖列表 |

---

## 下一步

- [安装指南](./INSTALLATION.md) - 环境搭建步骤
- [Docker 部署](../deployment/DOCKER.md) - 容器化部署
- [常见问题](./TROUBLESHOOTING.md) - 问题排查
