# 安装指南

本文档详细说明 LLM Agent 数据分析平台的安装步骤。

## 目录

- [环境要求](#环境要求)
- [数据库配置](#数据库配置)
- [Python 环境配置](#python-环境配置)
- [Node.js 环境配置](#nodejs-环境配置)
- [启动服务](#启动服务)

---

## 环境要求

### 必需环境

| 软件 | 版本要求 | 用途 |
|------|---------|------|
| **Python** | 3.10+ | FastAPI 和 Flask 服务 |
| **Node.js** | 16+ | 前端服务和认证服务 |
| **MySQL** | 5.7+ / 8.0+ | 数据存储 |
| **Docker** | 20.10+ | CodeAct Agent 沙箱隔离（可选） |

### 推荐开发工具

- **IDE**: VS Code / PyCharm / WebStorm
- **数据库管理**: Navicat / DBeaver / MySQL Workbench
- **API 测试**: Postman / Apifox

---

## 数据库配置

### 1. 安装 MySQL

**Windows:**
1. 下载 [MySQL Community Server](https://dev.mysql.com/downloads/mysql/)
2. 运行安装程序，设置 root 密码
3. 选择 "Developer Default" 或 "Server only" 安装类型

**macOS:**
```bash
brew install mysql
brew services start mysql
```

**Linux (Ubuntu):**
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

### 2. 创建数据库并导入数据

```bash
# 使用命令行导入
mysql -u root -p < movie_db.sql
```

验证导入成功：
```sql
mysql -u root -p
USE movie_db;
SHOW TABLES;
-- 应该看到 11 张表
```

### 3. 创建只读用户（安全隔离）

```sql
-- 创建只读用户
CREATE USER 'readonly_user'@'localhost' IDENTIFIED BY 'your_readonly_password';

-- 授予只读权限
GRANT SELECT ON movie_db.* TO 'readonly_user'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;
```

---

## Python 环境配置

### 1. 安装 Python

**Windows:**
1. 下载 [Python 3.10+](https://www.python.org/downloads/)
2. 安装时勾选 "Add Python to PATH"

**macOS:**
```bash
brew install python@3.10
```

**Linux:**
```bash
sudo apt install python3.10 python3.10-venv python3-pip
```

### 2. 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. 安装依赖

```bash
# 安装所有 Python 依赖
pip install -r requirements.txt

# 如果下载速度慢，使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## Node.js 环境配置

### 1. 安装 Node.js

**Windows:**
1. 下载 [Node.js LTS](https://nodejs.org/)
2. 运行安装程序

**macOS:**
```bash
brew install node@16
```

**Linux:**
```bash
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install nodejs
```

### 2. 安装依赖

```bash
cd Web_Node
npm install

# 如果下载速度慢，使用淘宝镜像
npm install --registry=https://registry.npmmirror.com
```

---

## 启动服务

项目采用三端微服务架构，需要启动三个服务。

### 1. 启动 Node.js 服务（端口 3000）

```bash
cd Web_Node
node app.js
```

**成功标志:**
```
服务器运行在 http://localhost:3000
数据库连接成功
```

### 2. 启动 Flask 服务（端口 5000）

```bash
cd Flask
python app2.py
```

**成功标志:**
```
随机森林模型加载成功！
LightGBM模型加载成功！
 * Running on http://127.0.0.1:5000
```

### 3. 启动 FastAPI 服务（端口 8000）

```bash
cd fastapi
uvicorn app3:app --reload
```

**成功标志:**
```
数据库连接成功，可用表: ['movies', 'users', 'logs', ...]
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 4. 访问前端页面

| 页面 | URL | 说明 |
|------|-----|------|
| 数据大屏 | http://localhost:3000/demo.html | 电影数据可视化 |
| 登录页 | http://localhost:3000/login.html | 用户登录 |
| 注册页 | http://localhost:3000/register.html | 用户注册 |
| 后台管理 | http://localhost:3000/admin.html | 管理员界面 |
| 数据分析 | http://localhost:3000/analyst.html | 数据分析师界面 |

### 5. 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin3 | 123456 | admin |
| user1 | 123456 | user |

---

## 下一步

- [配置说明](./CONFIGURATION.md) - 了解环境变量配置
- [Docker 部署](../deployment/DOCKER.md) - 使用 Docker 一键部署
- [常见问题](./TROUBLESHOOTING.md) - 问题排查
