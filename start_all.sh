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
osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR/fastapi' && uvicorn main:app --reload\""
sleep 3

echo "[4/5] qidong nginx-exporter (duankou 9113)..."
osascript -e "tell application \"Terminal\" to do script \"D:/app/nginx-exporter/nginx-prometheus-exporter.exe -nginx.scrape-uri http://localhost:80/nginx_status\""
sleep 3

echo "[5/5] qidong Prometheus (duankou 9090)..."
osascript -e "tell application \"Terminal\" to do script \"cd 'D:/app/permetheus/prometheus-3.4.0.windows-amd64' && ./prometheus.exe --config.file=prometheus.yml\""

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
