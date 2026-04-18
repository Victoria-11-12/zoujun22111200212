#!/bin/bash

echo "========================================"
echo "电影数据分析系统 - 一键启动脚本"
echo "========================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "[1/3] 启动 Node.js 服务 (端口 3000)..."
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT_DIR/Web_Node' && node app.js\""
sleep 3

echo "[2/3] 启动 Flask 服务 (端口 5000)..."
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT_DIR/Flask' && python app2.py\""
sleep 3

echo "[3/3] 启动 FastAPI 服务 (端口 8000)..."
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT_DIR/fastapi' && uvicorn app3:app --reload\""

echo ""
echo "========================================"
echo "所有服务启动完成！"
echo "========================================"
echo ""
echo "访问地址:"
echo "  - 数据大屏: http://localhost:3000/demo.html"
echo "  - 登录页面: http://localhost:3000/login.html"
echo "  - 后台管理: http://localhost:3000/admin.html"
echo "  - API文档:  http://localhost:8000/docs"
echo ""
echo "默认账号:"
echo "  - 管理员: admin3 / 123456"
echo "  - 普通用户: user1 / 123456"
echo ""
