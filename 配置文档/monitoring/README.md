# 可观测性监控部署指南

本文档说明如何为项目部署 Prometheus + Grafana + nginx-exporter 监控组件。

提供两种部署方式：**本地部署**（Windows 直接运行）和 **Docker 部署**（容器化），按需选择。

---

## 目录

- [组件说明](#组件说明)
- [端口规划](#端口规划)
- [方式一：本地部署（Windows）](#方式一本地部署windows)
- [方式二：Docker 部署](#方式二docker-部署)
- [Grafana 配置](#grafana-配置)
- [故障排查](#故障排查)

---

## 组件说明

| 组件 | 作用 | 下载地址 |
|------|------|---------|
| **Prometheus** | 时序数据库，定时抓取并存储监控指标 | [prometheus.io](https://prometheus.io/download/) |
| **Grafana** | 可视化面板，连接 Prometheus 渲染图表 | [grafana.com](https://grafana.com/grafana/download) |
| **nginx-exporter** | 将 Nginx stub_status 转换为 Prometheus 格式 | [GitHub Releases](https://github.com/nginxinc/nginx-prometheus-exporter/releases) |

**数据流向：** Nginx → nginx-exporter → Prometheus → Grafana

---

## 端口规划

| 服务 | 默认端口 | 说明 |
|------|---------|------|
| Nginx | 80 | 反向代理（主项目） |
| Node.js | 3000 | 业务服务（主项目） |
| Prometheus | 9090 | 监控数据查询 |
| Grafana | **3001** | 可视化面板（避免与 Node.js 3000 冲突） |
| nginx-exporter | 9113 | 指标转换器 |

---

## 前置要求：Nginx 启用 stub_status

监控组件依赖 Nginx 的 `/nginx_status` 端点。确认 `nginx.conf` 中包含以下配置：

```nginx
location /nginx_status {
    stub_status on;
    access_log off;
    allow 127.0.0.1;
    deny all;
}
```

验证端点可用：

```bash
curl http://localhost/nginx_status
# 应返回：
# Active connections: 1
# server accepts handled requests
#  3 3 6
# Reading: 0 Writing: 1 Waiting: 0
```

---

## 方式一：本地部署（Windows）

适用于 Windows 本地开发环境，直接运行各组件的可执行文件。

### 第 1 步：下载并解压

将三个组件下载后解压到任意目录，例如：

```
D:\app\
├── nginx\nginx-1.30.0\
├── permetheus\prometheus-3.4.0.windows-amd64\
├── grafana\grafana-13.0.1\
└── nginx-exporter\nginx-prometheus-exporter.exe
```

### 第 2 步：配置 Prometheus

编辑 Prometheus 目录下的 `prometheus.yml`：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Prometheus 自身监控
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
        labels:
          app: "prometheus"

  # Nginx 状态监控（通过 nginx-exporter）
  - job_name: "nginx"
    static_configs:
      - targets: ["localhost:9113"]
        labels:
          app: "nginx"

  # 后端服务监控（需在各服务中实现 /metrics 端点后取消注释）
  # - job_name: "nodejs"
  #   static_configs:
  #     - targets: ["localhost:3000"]
  #       labels:
  #         app: "nodejs"
  #
  # - job_name: "flask"
  #   static_configs:
  #     - targets: ["localhost:5000"]
  #       labels:
  #         app: "flask"
  #
  # - job_name: "fastapi"
  #   static_configs:
  #     - targets: ["localhost:8000"]
  #       labels:
  #         app: "fastapi"
```

### 第 3 步：配置 Grafana 端口

Grafana 默认端口为 3000，会与 Node.js 冲突。编辑 `conf/defaults.ini`：

```ini
[server]
http_port = 3001
```

### 第 4 步：启动（一键脚本）

在项目根目录创建 `start_monitoring.bat`：

```bat
@echo off
chcp 65001 >nul
echo ========================================
echo 监控组件一键启动
echo ========================================
echo.

echo [1/3] 启动 nginx-exporter (端口 9113)...
start "Nginx Exporter" cmd /k "D:\app\nginx-exporter\nginx-prometheus-exporter.exe -nginx.scrape-uri http://localhost:80/nginx_status"
timeout /t 2 >nul

echo [2/3] 启动 Prometheus (端口 9090)...
start "Prometheus" cmd /k "cd /d D:\app\permetheus\prometheus-3.4.0.windows-amd64 && prometheus.exe --config.file=prometheus.yml"
timeout /t 2 >nul

echo [3/3] 启动 Grafana (端口 3001)...
start "Grafana" cmd /k "cd /d D:\app\grafana\grafana-13.0.1+security-01 && .\bin\grafana.exe server -config .\conf\defaults.ini -homepath ."
timeout /t 2 >nul

echo.
echo ========================================
echo 监控组件已启动
echo ========================================
echo   - Prometheus:  http://localhost:9090
echo   - Grafana:     http://localhost:3001
echo   - Exporter:    http://localhost:9113/metrics
echo.
pause
```

> 请根据实际安装路径修改脚本中的目录。

### 第 5 步：验证

浏览器访问 http://localhost:9090/targets ，确认 `nginx` 和 `prometheus` 两个 target 状态为 **UP**。

---

## 方式二：Docker 部署

适用于服务器生产环境，通过 Docker Compose 统一管理。

### 第 1 步：确认主项目已运行

监控组件需加入主项目的 Docker 网络：

```bash
# 确认主项目容器状态
docker compose -f ../deployment/docker-compose.yml ps

# 确认网络存在
docker network ls | grep movie_network
```

### 第 2 步：进入监控目录并启动

```bash
cd 配置文档/monitoring

# 启动
docker compose -f docker-compose.monitoring.yml up -d

# 查看状态
docker compose -f docker-compose.monitoring.yml ps
```

等待看到以下输出表示启动成功：

```
NAME                    STATUS          PORTS
movie_prometheus        Up (healthy)    0.0.0.0:9090->9090/tcp
movie_grafana           Up (healthy)    0.0.0.0:3001->3000/tcp
movie_nginx_exporter    Up (healthy)    0.0.0.0:9113->9113/tcp
```

### 第 3 步：验证

```bash
# 验证 Prometheus 抓取目标
curl http://localhost:9090/api/v1/targets
# nginx-exporter 的 state 应为 "up"

# 验证 nginx-exporter 指标
curl http://localhost:9113/metrics
```

### 常用命令

```bash
# 启动
docker compose -f docker-compose.monitoring.yml up -d

# 停止
docker compose -f docker-compose.monitoring.yml down

# 查看日志
docker compose -f docker-compose.monitoring.yml logs -f

# 重启某个服务
docker compose -f docker-compose.monitoring.yml restart grafana

# 停止并删除数据卷（监控历史数据会丢失）
docker compose -f docker-compose.monitoring.yml down -v
```

---

## Grafana 配置

### 1. 登录

浏览器访问：http://localhost:3001

| 用户名 | 密码 |
|--------|------|
| admin | admin |

> 首次登录会提示修改密码，可跳过。

### 2. 添加 Prometheus 数据源

1. 左侧菜单 → **Connections** → **Data sources**
2. 点击 **Add data source** → 选择 **Prometheus**
3. 填写 URL：
   - **本地部署**：`http://localhost:9090`
   - **Docker 部署**：`http://prometheus:9090`（容器内部通信，填容器名）
4. 点击 **Save & test**，显示 "Data source is working" 表示成功

### 3. 导入 Nginx 监控面板

1. 左侧菜单 → **Dashboards** → **Import**
2. 输入面板 ID：**12708**（Nginx 监控面板）
3. 点击 **Load**
4. 选择刚创建的 Prometheus 数据源
5. 点击 **Import**

导入后即可看到 Nginx 的连接数、请求速率、读写状态等实时监控图表。

---

## 故障排查

### nginx-exporter 状态为 DOWN

**原因：** Nginx 未启用 `stub_status` 端点，或 Nginx 未启动。

**解决方案：**
1. 确认 `nginx.conf` 中已添加 `/nginx_status` 配置
2. 确认 Nginx 正在运行：`curl http://localhost/nginx_status`
3. 确认 nginx-exporter 启动参数中 `-nginx.scrape-uri` 地址正确

### Grafana 无法连接 Prometheus

**本地部署：** URL 填 `http://localhost:9090`

**Docker 部署：** URL 必须填 `http://prometheus:9090`（容器名），不能填 `http://localhost:9090`

### Grafana 端口 3001 无法访问

1. 确认 Grafana 已启动（检查 3001 端口是否被监听）
2. 云服务器需在安全组/防火墙中放行 3001 端口
3. 本地部署确认 `defaults.ini` 中 `http_port = 3001`

### Docker 启动报错 "network movie_network not found"

主项目 Docker 网络未创建，先启动主项目：

```bash
cd ../deployment
docker compose up -d
```

---

## 下一步

- [Nginx 配置](../nginx/nginx.conf) - 反向代理配置参考
- [Docker 部署](../deployment/DOCKER.md) - 主项目部署指南
- [配置说明](../guides/CONFIGURATION.md) - 环境变量详细说明
