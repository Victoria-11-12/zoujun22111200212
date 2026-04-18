# 项目配置文档

本文档详细说明了电影数据分析与 AI 智能问答系统的完整配置流程，帮助您快速复现项目。

---

## 📋 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [详细配置步骤](#详细配置步骤)
  - [1. 数据库配置](#1-数据库配置)
  - [2. Python 环境配置](#2-python-环境配置)
  - [3. Node.js 环境配置](#3-nodejs-环境配置)
  - [4. 环境变量配置](#4-环境变量配置)
  - [5. Docker 配置](#5-docker-配置)
  - [6. 机器学习模型准备](#6-机器学习模型准备)
  - [7. 启动服务](#7-启动服务)
- [Docker 部署（可选）](#docker-部署可选)
- [一键启动脚本](#一键启动脚本)
- [配置文件清单](#配置文件清单)
- [常见问题](#常见问题)

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

## 快速开始

如果您熟悉相关技术栈，可以按照以下步骤快速启动：

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd bishe_zoujun

# 2. 导入数据库
mysql -u root -p < 配置文档/movie_db.sql

# 3. 配置环境变量
cp 配置文档/.env.example fastapi/.env
# 编辑 fastapi/.env 填写实际配置

# 4. 安装 Python 依赖
pip install -r 配置文档/requirements.txt

# 5. 安装 Node.js 依赖
cd Web_Node
npm install
cd ..

# 6. 启动服务（需要三个终端窗口）
# 终端1: Node.js 服务
cd Web_Node && node app.js

# 终端2: Flask 服务
cd Flask && python app2.py

# 终端3: FastAPI 服务
cd fastapi && uvicorn app3:app --reload
```

---

## 详细配置步骤

### 1. 数据库配置

#### 1.1 安装 MySQL

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

#### 1.2 创建数据库并导入数据

```bash
# 方式1: 使用命令行导入
mysql -u root -p < 配置文档/movie_db.sql

# 方式2: 登录 MySQL 后导入
mysql -u root -p
```

```sql
-- 在 MySQL 命令行中执行
source d:/bishe_zoujun/配置文档/movie_db.sql;

-- 验证导入成功
USE movie_db;
SHOW TABLES;
-- 应该看到 10 张表
```

#### 1.3 创建只读用户（安全隔离）

为了实现数据库权限隔离，需要创建只读用户：

```sql
-- 创建只读用户
CREATE USER 'readonly_user'@'localhost' IDENTIFIED BY 'your_readonly_password';

-- 授予只读权限
GRANT SELECT ON movie_db.* TO 'readonly_user'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 验证权限
SHOW GRANTS FOR 'readonly_user'@'localhost';
```

#### 1.4 数据库表结构说明

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

### 2. Python 环境配置

#### 2.1 安装 Python

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

#### 2.2 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

#### 2.3 安装依赖

```bash
# 安装所有 Python 依赖
pip install -r 配置文档/requirements.txt

# 如果下载速度慢，使用国内镜像
pip install -r 配置文档/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 2.4 依赖包说明

| 包名 | 版本 | 用途 |
|------|------|------|
| `fastapi` | 0.115.12 | FastAPI 框架 |
| `uvicorn` | 0.34.0 | ASGI 服务器 |
| `langchain` | 0.3.23 | LLM 应用框架 |
| `langchain-openai` | 0.3.14 | OpenAI 集成 |
| `langchain-deepseek` | 0.1.3 | DeepSeek 集成 |
| `pymysql` | 1.1.1 | MySQL 驱动 |
| `bcrypt` | 4.3.0 | 密码加密 |
| `docker` | 7.1.0 | Docker SDK |
| `pyecharts` | 2.0.8 | 图表库 |
| `flask` | 3.1.0 | Flask 框架 |
| `scikit-learn` | 1.6.1 | 机器学习 |
| `lightgbm` | 4.6.0 | 梯度提升树 |

---

### 3. Node.js 环境配置

#### 3.1 安装 Node.js

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

#### 3.2 安装依赖

```bash
cd Web_Node
npm install

# 如果下载速度慢，使用淘宝镜像
npm install --registry=https://registry.npmmirror.com
```

#### 3.3 依赖包说明

| 包名 | 版本 | 用途 |
|------|------|------|
| `express` | ^5.2.1 | Web 框架 |
| `mysql2` | ^3.18.2 | MySQL 驱动 |
| `jsonwebtoken` | ^9.0.3 | JWT 认证 |
| `bcryptjs` | ^3.0.3 | 密码加密 |
| `cors` | ^2.8.6 | 跨域支持 |
| `dotenv` | ^17.3.1 | 环境变量 |
| `axios` | ^1.13.6 | HTTP 客户端 |

---

### 4. 环境变量配置

#### 4.1 创建 .env 文件

```bash
# 复制模板文件
cp 配置文档/.env.example fastapi/.env

# 编辑配置文件
# Windows:
notepad fastapi/.env
# macOS/Linux:
nano fastapi/.env
```

#### 4.2 必填配置项

```env
# 数据库配置（必填）
DB_HOST=localhost
DB_PORT=3306
DB_NAME=movie_db
DB_USER=root
DB_PASS=your_mysql_password

# 只读用户配置（必填，用于权限隔离）
DB_USER_READONLY=readonly_user
DB_PASS_READONLY=your_readonly_password

# LLM API 配置（必填）
API_BASE=https://api.deepseek.com
API_KEY=your_deepseek_api_key
MODEL_NAME=deepseek-chat
```

#### 4.3 获取 DeepSeek API Key

1. 访问 [DeepSeek 官网](https://www.deepseek.com/)
2. 注册账号并登录
3. 进入 [API Keys 页面](https://platform.deepseek.com/api_keys)
4. 点击 "创建 API Key"
5. 复制 API Key 并填入 `.env` 文件

**费用说明:**
- DeepSeek Chat: ¥1/百万 tokens（输入），¥2/百万 tokens（输出）
- 新用户赠送 ¥10 体验金

#### 4.4 可选配置项

```env
# 评估模型配置（数据分析师模块需要）
EVAL_API_KEY=your_eval_api_key
EVAL_MODEL_NAME=deepseek-reasoner

# JWT 配置（Node.js 服务）
JWT_SECRET=your_random_secret_string
JWT_EXPIRES_IN=24

# Docker 配置（CodeAct Agent 需要）
DOCKER_IMAGE=pyecharts-sandbox
DOCKER_MEMORY_LIMIT=256
DOCKER_TIMEOUT=30
```

---

### 5. Docker 配置

Docker 用于 CodeAct Agent 的沙箱隔离，防止恶意代码执行。

#### 5.1 安装 Docker

**Windows:**
1. 下载 [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. 运行安装程序
3. 重启电脑后启动 Docker Desktop

**macOS:**
```bash
brew install --cask docker
```

**Linux:**
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

#### 5.2 创建 pyecharts 沙箱镜像

```bash
# 进入 fastapi 目录
cd fastapi

# 构建镜像
docker build -t pyecharts-sandbox .

# 验证镜像创建成功
docker images | grep pyecharts-sandbox
```

#### 5.3 Dockerfile 说明

项目已提供 `fastapi/Dockerfile`，内容如下：

```dockerfile
FROM m.daocloud.io/docker.io/library/python:3.10-slim

RUN pip install pyecharts pandas numpy --no-cache-dir

WORKDIR /app
```

**镜像特性:**
- 基于 Python 3.10-slim（轻量级）
- 预装 pyecharts、pandas、numpy
- 工作目录 `/app`

#### 5.4 安全配置

CodeAct Agent 在 Docker 容器中执行代码时，会应用以下安全限制：

| 限制项 | 配置 | 说明 |
|--------|------|------|
| 网络禁用 | `network_disabled=True` | 容器无法访问外部网络 |
| 内存限制 | `mem_limit='256m'` | 限制内存使用 |
| 执行超时 | `timeout=30` | 30秒超时 |
| 只读文件系统 | `read_only=True` | 禁止写入文件 |

---

### 6. 机器学习模型准备

#### 6.1 模型文件位置

项目已包含训练好的模型文件：

```
Flask/
├── random_forest_model.pkl    # 随机森林模型（黑马筛选）
└── lightgbm_model_1.pkl       # LightGBM 模型（票房预测）
```

#### 6.2 模型说明

| 模型 | 文件 | 用途 | 特征 |
|------|------|------|------|
| **随机森林** | random_forest_model.pkl | 黑马电影筛选 | budget, director_facebook_likes, actor_facebook_likes, imdb_score 等 |
| **LightGBM** | lightgbm_model_1.pkl | 票房预测 | budget, genres, New_Director, New_Actor |

#### 6.3 重新训练模型（可选）

如果需要重新训练模型，可以运行 Jupyter Notebook：

```bash
# 安装 Jupyter
pip install jupyter

# 启动 Jupyter
cd Flask
jupyter notebook

# 打开对应的 .ipynb 文件
# - random_forert.ipynb: 随机森林训练
# - lightgbm.ipynb: LightGBM 训练
```

---

### 7. 启动服务

项目采用三端微服务架构，需要启动三个服务。

#### 7.1 启动 Node.js 服务（端口 3000）

```bash
# 打开终端1
cd Web_Node
node app.js
```

**成功标志:**
```
服务器运行在 http://localhost:3000
数据库连接成功
```

**功能:**
- 用户认证（注册、登录）
- JWT 签发
- 数据接口
- 操作日志

#### 7.2 启动 Flask 服务（端口 5000）

```bash
# 打开终端2
cd Flask
python app2.py
```

**成功标志:**
```
随机森林模型加载成功！
LightGBM模型加载成功！
 * Running on http://127.0.0.1:5000
```

**功能:**
- 票房预测
- 黑马推荐
- ROI 分析

#### 7.3 启动 FastAPI 服务（端口 8000）

```bash
# 打开终端3
cd fastapi
uvicorn app3:app --reload
```

**成功标志:**
```
数据库连接成功，可用表: ['movies', 'users', 'logs', ...]
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**功能:**
- ReAct SQL Agent
- CodeAct Agent
- 意图路由
- 安全检测
- 操作回滚
- LLM 评估

#### 7.4 访问前端页面

启动所有服务后，访问以下页面：

| 页面 | URL | 说明 |
|------|-----|------|
| 数据大屏 | http://localhost:3000/demo.html | 电影数据可视化 |
| 登录页 | http://localhost:3000/login.html | 用户登录 |
| 注册页 | http://localhost:3000/register.html | 用户注册 |
| 后台管理 | http://localhost:3000/admin.html | 管理员界面 |
| 数据分析 | http://localhost:3000/analyst.html | 数据分析师界面 |

#### 7.5 默认账号

数据库中已包含测试账号：

| 用户名 | 密码 | 角色 | 权限 |
|--------|------|------|------|
| admin3 | 123456 | admin | 增删改查 |
| user1 | 123456 | user | 查询+绘图 |

---

## 常见问题

### Q1: 数据库连接失败

**错误信息:**
```
pymysql.err.OperationalError: (1045, "Access denied for user 'root'@'localhost'")
```

**解决方案:**
1. 检查 `.env` 文件中的 `DB_USER` 和 `DB_PASS` 是否正确
2. 确认 MySQL 服务已启动
3. 尝试在命令行手动连接: `mysql -u root -p`

### Q2: LLM API 调用失败

**错误信息:**
```
openai.AuthenticationError: Incorrect API key provided
```

**解决方案:**
1. 检查 `.env` 文件中的 `API_KEY` 是否正确
2. 确认 API Key 有效且有余额
3. 检查 `API_BASE` 地址是否正确

### Q3: Docker 容器启动失败

**错误信息:**
```
docker.errors.ImageNotFound: pyecharts-sandbox
```

**解决方案:**
```bash
# 重新构建镜像
cd fastapi
docker build -t pyecharts-sandbox .
```

### Q4: 模型加载失败

**错误信息:**
```
FileNotFoundError: random_forest_model.pkl
```

**解决方案:**
1. 确认模型文件存在于 `Flask/` 目录
2. 检查文件名是否正确
3. 如果文件丢失，需要重新训练模型

### Q5: 端口被占用

**错误信息:**
```
OSError: [Errno 98] Address already in use: ('0.0.0.0', 3000)
```

**解决方案:**

**Windows:**
```bash
# 查找占用端口的进程
netstat -ano | findstr :3000
# 结束进程（PID 为上面查到的进程ID）
taskkill /PID <PID> /F
```

**macOS/Linux:**
```bash
# 查找并结束进程
lsof -i :3000
kill -9 <PID>
```

### Q6: 前端页面无法访问后端 API

**错误信息:**
```
CORS policy: No 'Access-Control-Allow-Origin' header
```

**解决方案:**
1. 确认三个服务都已启动
2. 检查服务端口是否正确（3000/5000/8000）
3. 清除浏览器缓存后重试

### Q7: Python 依赖安装失败

**错误信息:**
```
error: Microsoft Visual C++ 14.0 is required
```

**解决方案:**
1. 安装 [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. 或使用预编译的 wheel 文件:
   ```bash
   pip install --only-binary :all: <package_name>
   ```

---

## 项目目录结构

```
bishe_zoujun/
├── Flask/                      # Flask 机器学习服务
│   ├── app2.py                 # Flask 主程序
│   ├── data_all/               # 数据文件
│   │   ├── movie1.xlsx         # 数据集1
│   │   ├── movie2.xlsx         # 数据集2
│   │   ├── movie3.xlsx         # 数据集3
│   │   └── movies_all_cleaned.csv  # 清洗后数据
│   ├── random_forest_model.pkl # 随机森林模型
│   ├── lightgbm_model_1.pkl    # LightGBM 模型
│   ├── random_forert.ipynb     # 随机森林训练
│   ├── lightgbm.ipynb          # LightGBM 训练
│   └── qingxi.ipynb            # 数据清洗
│
├── Web_Node/                   # Node.js 前端服务
│   ├── app.js                  # Node.js 主程序
│   ├── package.json            # Node.js 依赖
│   ├── css/                    # 样式文件
│   ├── js/                     # JavaScript 文件
│   ├── img/                    # 图片资源
│   ├── video/                  # 视频资源
│   ├── demo.html               # 数据大屏
│   ├── login.html              # 登录页
│   ├── register.html           # 注册页
│   ├── admin.html              # 管理员页
│   └── analyst.html            # 数据分析师页
│
├── fastapi/                    # FastAPI AI Agent 服务
│   ├── app3.py                 # FastAPI 主程序
│   ├── Dockerfile              # Docker 配置
│   └── .env                    # 环境变量（需创建）
│
├── 配置文档/                   # 配置文档目录
│   ├── movie_db.sql            # 数据库 SQL 文件
│   ├── requirements.txt        # Python 依赖
│   ├── .env.example            # 环境变量模板
│   └── CONFIG.md               # 本配置文档
│
├── 更新日志/                   # 开发日志
│   └── 2026-04-*.md            # 每日更新记录
│
├── README.md                   # 项目说明
├── .gitignore                  # Git 忽略文件
└── .gitattributes              # Git 属性
```

---

## Docker 部署（可选）

如果您希望使用 Docker 一键部署整个系统，可以使用 Docker Compose。

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+

### 部署步骤

#### 1. 配置环境变量

```bash
# 创建环境变量文件
cd 配置文档
cp .env.example .env

# 编辑 .env 文件，填写实际配置
nano .env
```

#### 2. 启动所有服务

```bash
# 在配置文档目录下执行
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 3. 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 数据大屏 | http://localhost:3000/demo.html | 前端页面 |
| 登录页 | http://localhost:3000/login.html | 用户登录 |
| 后台管理 | http://localhost:3000/admin.html | 管理员界面 |
| API 文档 | http://localhost:8000/docs | FastAPI 文档 |

#### 4. 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

### Docker Compose 配置说明

项目提供了 `docker-compose.yml` 文件，包含以下服务：

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| mysql | movie_mysql | 3306 | MySQL 8.0 数据库 |
| nodejs | movie_nodejs | 3000 | Node.js 认证服务 |
| flask | movie_flask | 5000 | Flask 机器学习服务 |
| fastapi | movie_fastapi | 8000 | FastAPI AI Agent 服务 |

### 数据持久化

Docker Compose 会创建以下数据卷：

- `mysql_data`: MySQL 数据持久化

### 注意事项

1. **首次启动**: 首次启动会自动导入 `movie_db.sql`，需要等待几分钟
2. **API Key**: 必须在 `.env` 文件中配置 `API_KEY`，否则 FastAPI 服务无法正常工作
3. **内存要求**: 建议至少 4GB 内存，推荐 8GB
4. **网络**: 确保宿主机端口 3000/5000/8000/3306 未被占用

---

## 一键启动脚本

项目提供了便捷的一键启动脚本，无需手动开启多个终端。

### Windows 用户

```bash
# 双击运行或在命令行执行
配置文档\start_all.bat
```

脚本会自动：
1. 启动 Node.js 服务（新窗口）
2. 启动 Flask 服务（新窗口）
3. 启动 FastAPI 服务（新窗口）

### macOS 用户

```bash
# 添加执行权限
chmod +x 配置文档/start_all.sh

# 运行脚本
./配置文档/start_all.sh
```

脚本会自动在三个新的终端窗口中启动三个服务。

### 注意事项

1. **环境准备**: 运行脚本前，请确保已完成所有环境配置
2. **依赖安装**: 确保已安装所有 Python 和 Node.js 依赖
3. **数据库**: 确保 MySQL 服务已启动且数据库已导入
4. **环境变量**: 确保 `fastapi/.env` 文件已正确配置

---

## 配置文件清单

项目提供了以下配置文件，方便快速复现：

| 文件 | 位置 | 说明 |
|------|------|------|
| `movie_db.sql` | 配置文档/ | 数据库结构和初始数据 |
| `requirements.txt` | 配置文档/ | Python 依赖列表 |
| `.env.example` | 配置文档/ | 环境变量模板 |
| `CONFIG.md` | 配置文档/ | 本配置文档 |
| `docker-compose.yml` | 配置文档/ | Docker Compose 配置 |
| `start_all.bat` | 配置文档/ | Windows 一键启动脚本 |
| `start_all.sh` | 配置文档/ | macOS 一键启动脚本 |
| `Dockerfile` | fastapi/ | FastAPI Docker 配置 |
| `Dockerfile` | Web_Node/ | Node.js Docker 配置 |
| `requirements.txt` | Flask/ | Flask 服务依赖 |

---

## 技术支持

如有问题，请参考：

1. **项目 README**: [README.md](../README.md)
2. **更新日志**: [更新日志/](../更新日志/)
3. **API 文档**: 启动 FastAPI 后访问 http://localhost:8000/docs

---

**祝您使用愉快！**
