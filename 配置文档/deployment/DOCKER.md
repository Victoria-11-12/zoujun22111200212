# Docker 部署指南

本文档详细说明如何使用 Docker Compose 部署项目。

**Docker 部署 vs 本地开发：**
- **Docker 部署**：适合快速体验或生产环境，无需安装 Python/Node.js/MySQL，一键启动所有服务
- **本地开发**：适合二次开发，需要安装各种环境，详见 [安装指南](../guides/INSTALLATION.md)

---

## 目录

- [前置要求](#前置要求)
- [安装 Docker](#安装-docker)
- [部署步骤](#部署步骤)
- [验证部署](#验证部署)
- [常用命令](#常用命令)
- [故障排查](#故障排查)

---

## 前置要求

- Windows 10/11、macOS 或 Linux 系统
- 至少 4GB 内存（推荐 8GB）
- 20GB 可用磁盘空间

---

## 安装 Docker

### Windows 安装

1. 访问 [Docker Desktop 下载页面](https://www.docker.com/products/docker-desktop)
2. 点击 "Download for Windows" 下载安装包
3. 双击安装包，按提示完成安装
4. 重启电脑
5. 打开 Docker Desktop，等待显示 "Docker Desktop is running"

验证安装：
```bash
docker --version
docker compose version
```

### macOS 安装

```bash
# 使用 Homebrew 安装
brew install --cask docker

# 启动 Docker Desktop
open /Applications/Docker.app
```

### Linux 安装（Ubuntu）

```bash
# 安装 Docker（Docker Compose v2 已内置）
curl -fsSL https://get.docker.com | sh

# 将当前用户加入 docker 组
sudo usermod -aG docker $USER

# 重新登录或执行
newgrp docker
```

---

## 部署步骤

### 第1步：克隆项目

```bash
# 克隆项目到本地
git clone https://github.com/Victoria-11-12/zoujun22111200212.git

# 进入项目目录
cd zoujun22111200212
```

### 第2步：进入配置文档目录

```bash
cd 配置文档/deployment
```

### 第3步：配置环境变量

```bash
# 复制环境变量模板到当前目录（Docker Compose 在此目录读取 .env）
cp ../.env.example ./.env

# 编辑 .env 文件
# Windows: 用记事本打开
notepad .env
# macOS/Linux: 用 nano 或 vim
nano .env
```

必须修改的配置项：
```env
# LLM API 密钥（必填，否则无法使用AI功能）
API_KEY=your_deepseek_api_key
```

可选修改的配置项：
```env
# 数据库密码（不修改则使用默认123456）
DB_PASS=your_mysql_password
```

获取 DeepSeek API Key：
1. 访问 https://platform.deepseek.com/
2. 注册账号并登录
3. 进入 "API Keys" 页面
4. 点击 "创建 API Key"
5. 复制密钥填入 `.env` 文件

### 第4步：构建 PyEcharts 沙箱镜像（用于AI绘图）

```bash
# 构建沙箱镜像（用于在线绘图功能）
docker build -t pyecharts-sandbox ../../fastapi
```

### 第5步：启动服务

```bash
# 在 deployment 目录下执行
# Docker Compose v1（已弃用，部分旧系统仍有）
docker-compose up -d
# Docker Compose v2（新版 Docker 默认）
docker compose up -d
```

首次启动会执行：
1. 下载 MySQL、Node.js、Python 镜像（约 5-10 分钟，取决于网速）
2. 构建三个服务的 Docker 镜像
3. 启动 MySQL 并导入数据库
4. 启动 Node.js、Flask、FastAPI 服务

查看启动进度：
```bash
# 查看所有服务状态
docker compose ps

# 查看实时日志
docker compose logs -f

# 只看某个服务的日志
docker compose logs -f fastapi
```

等待看到以下输出表示启动成功：
```
Name                Command                  State           Ports
-----------------------------------------------------------------------------
movie_fastapi       "python main.py"         Up (healthy)    0.0.0.0:8000->8000/tcp
movie_flask         "python app2.py"         Up (healthy)    0.0.0.0:5000->5000/tcp
movie_mysql         "docker-entrypoint.s…"   Up (healthy)    0.0.0.0:3306->3306/tcp
movie_web_node      "docker-entrypoint.s…"   Up (healthy)    0.0.0.0:3000->3000/tcp
```

---

## 验证部署

### 访问前端页面

打开浏览器，访问：http://localhost:3000

应该看到登录页面。

### 测试默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin3 | 123456 | 管理员 |
| user1 | 123456 | 普通用户 |

### 测试 AI 对话

1. 用 user1 登录
2. 进入 AI 对话页面
3. 输入："查询票房最高的5部电影"
4. 应该返回电影列表

### 查看 API 文档

访问：http://localhost:8000/docs

可以看到 FastAPI 自动生成的 API 文档。

---

## 常用命令

```bash
# 查看所有服务状态
docker compose ps

# 查看所有日志
docker compose logs

# 查看某个服务的日志
docker compose logs fastapi
docker compose logs flask
docker compose logs web_node
docker compose logs mysql

# 实时跟踪日志
docker compose logs -f

# 重启某个服务
docker compose restart fastapi

# 停止所有服务
docker compose down

# 停止并删除数据（数据库数据会丢失）
docker compose down -v

# 进入容器内部调试
docker compose exec mysql bash
docker compose exec fastapi bash

# 重新构建镜像
docker compose build

# 重新构建并启动
docker compose up -d --build
```

---

## 故障排查

### 问题1：端口被占用

**错误信息：**
```
Error starting userland proxy: listen tcp 0.0.0.0:3306: bind: address already in use
```

**解决方案：**
```bash
# Windows: 查找并结束占用端口的进程
netstat -ano | findstr :3306
taskkill /PID <进程ID> /F

# 或修改 .env 文件，使用其他端口
DB_PORT=3307
```

### 问题2：API Key 未配置

**现象：** AI 对话返回错误或没有响应

**解决方案：**
```bash
# 1. 编辑 .env 文件，确保 API_KEY 已填写
notepad .env

# 2. 重启 FastAPI 服务
docker compose restart fastapi

# 3. 查看日志确认
docker compose logs fastapi
```

### 问题3：数据库连接失败

**错误信息：**
```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")
```

**解决方案：**
```bash
# 1. 查看 MySQL 容器状态
docker compose ps mysql

# 2. 查看 MySQL 日志
docker compose logs mysql

# 3. 等待 MySQL 完全启动（首次启动需要 1-2 分钟）
docker compose logs -f mysql
# 看到 "ready for connections" 表示启动完成

# 4. 如果失败，重启服务
docker compose restart
```

### 问题4：镜像下载慢

**解决方案：**
```bash
# 配置国内镜像加速器
# Windows/macOS: 打开 Docker Desktop -> Settings -> Docker Engine
# 添加以下配置：
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
```

### 问题 5：内存不足

**现象：** 容器频繁重启或启动失败

**解决方案：**
1. 关闭其他占用内存的程序
2. 增加 Docker Desktop 内存限制：
   - Windows/macOS: Docker Desktop -> Settings -> Resources -> Memory
   - 设置为 4GB 或更高

### 问题 6：Flask 模型加载失败（AttributeError: 'NoneType' object has no attribute 'predict'）

**错误信息：**
```
随机森林模型加载失败：118
LightGBM 模型加载失败：118
AttributeError: 'NoneType' object has no attribute 'predict'
```

**原因：** 机器学习模型文件（`.pkl`）使用 Git LFS 管理，服务器拉取代码时只下载了指针文件（128 字节），而非真实模型文件（3MB+）。

**解决方案：**

#### 方案 A：在服务器上配置 Git LFS（推荐）

```bash
# 1. 进入项目目录
cd /root/zoujun22111200212

# 2. 安装 Git LFS（CentOS/RHEL）
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.rpm.sh | sudo bash
sudo yum install -y git-lfs

# Ubuntu/Debian 使用：
# curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
# sudo apt-get install -y git-lfs

# 3. 初始化 Git LFS
git lfs install

# 4. 配置 GitHub 认证（使用 Personal Access Token）
git remote set-url origin https://YOUR_GITHUB_TOKEN@github.com/Victoria-11-12/zoujun22111200212.git

# 5. 拉取 LFS 管理的模型文件
git lfs pull

# 6. 确认模型文件已正确下载（应该从 128 字节变成 3MB 左右）
ls -lh Flask/*.pkl

# 7. 重新构建 Flask 镜像
docker compose -f 配置文档/deployment/docker-compose.yml build --no-cache flask

# 8. 重启 Flask 容器
docker compose -f 配置文档/deployment/docker-compose.yml up -d flask

# 9. 查看日志确认模型加载成功
docker logs movie_flask -f
```

看到以下日志表示成功：
```
随机森林模型加载成功！
LightGBM 模型加载成功！
```

#### 方案 B：在本地构建镜像后推送到服务器

```bash
# 1. 在本地电脑拉取 LFS 文件
git lfs pull

# 2. 确认模型文件已下载
ls -lh Flask/*.pkl

# 3. 构建 Flask 镜像
docker build -t movie_flask -f 配置文档/docker/Dockerfile.flask .

# 4. 导出镜像为 tar 文件
docker save movie_flask > flask_image.tar

# 5. 上传到服务器（使用 scp）
scp flask_image.tar root@服务器 IP:/root/

# 6. 在服务器上导入镜像
docker load < flask_image.tar

# 7. 重启 Flask 容器
docker compose -f 配置文档/deployment/docker-compose.yml up -d flask
```

#### 获取 GitHub Personal Access Token

1. 登录 https://github.com
2. 点击右上角头像 → Settings
3. 左侧 Developer settings → Personal access tokens → Tokens (classic)
4. 点击 **Generate new token (classic)**
5. Token name: 填写描述（如 `服务器`）
6. Expiration: 选择过期时间（如 90 天）
7. **必须勾选 `repo` 权限**（包含所有子权限）
8. 点击 **Generate token**
9. 复制生成的 token（以 `ghp_` 开头，立即保存，只显示一次）

**注意：** 不要使用 fine-grained token，这种不支持 Git LFS。

### 问题 7：AI 百度搜索功能提示 Chrome 未找到

**错误信息：**
```
打开百度百科失败：✗ Auto-launch failed: Chrome not found
```

**原因：** AI 的百度搜索功能需要调用 Chrome 浏览器，但当前环境中没有安装 Chrome。

**为什么 Docker 镜像中没有预装 Chrome：**

Google Chrome 浏览器体积较大（约 300-400MB），如果打包到镜像中，会导致：
1. 镜像体积显著增大，构建和下载时间变长
2. 每次部署都需要传输更大的镜像文件
3. 并非所有用户都需要百度搜索功能，强制安装会增加不必要的资源占用

因此，Chrome 浏览器采用按需安装的方式，由用户在宿主机上自行安装。

**解决方案：**

**在宿主机上安装 Chrome 浏览器**：

1. 访问 https://www.google.com/chrome/
2. 下载并安装 Chrome 浏览器
3. 刷新网页，重新尝试百度搜索功能

或者使用 Edge、Firefox 等其他浏览器（需要配置 `agent-browser` 支持）。

**注意：** 此功能不影响 AI 对话、数据可视化等其他功能，只在调用百度搜索时需要。

---

## 下一步

- [安装指南](../guides/INSTALLATION.md) - 本地开发环境搭建
- [配置说明](../guides/CONFIGURATION.md) - 环境变量详细说明
- [常见问题](../guides/TROUBLESHOOTING.md) - 更多问题排查
