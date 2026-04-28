#!/bin/bash

echo "========================================"
echo "dianying shuju fenxi xitong - yijian qidong"
echo "========================================"
echo ""

# huoqu jiaoben suozai mulu
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/3] qidong Node.js fuwu (duankou 3000)..."
osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR/Web_Node' && node app.js\""
sleep 3

echo "[2/3] qidong Flask fuwu (duankou 5000)..."
osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR/Flask' && python app2.py\""
sleep 3

echo "[3/3] qidong FastAPI fuwu (duankou 8000)..."
osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR/fastapi' && uvicorn app3:app --reload\""

echo ""
echo "========================================"
echo "suoyou fuwu yijing qidong"
echo "========================================"
echo ""
echo "fangwen dizhi:"
echo "  - dasha: http://localhost:3000/demo.html"
echo "  - denglu: http://localhost:3000/login.html"
echo "  - houtai: http://localhost:3000/admin.html"
echo "  - API: http://localhost:8000/docs"
echo ""
echo "moren zhanghao:"
echo "  - guanliyuan: admin3 / 123456"
echo "  - putong yonghu: user1 / 123456"
echo ""
