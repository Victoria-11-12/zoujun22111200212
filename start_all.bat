@echo off
chcp 65001 >nul
echo ========================================
echo dianying shuju fenxi xitong - yijian qidong
echo ========================================
echo.

echo [1/7] qidong Node.js fuwu (duankou 3000)...
start "Node.js Server" cmd /k "cd /d D:\bishe_zoujun\Web_Node && node app.js"
timeout /t 3 >nul

echo [2/7] qidong Flask fuwu (duankou 5000)...
start "Flask Server" cmd /k "cd /d D:\bishe_zoujun\Flask && python app2.py"
timeout /t 3 >nul

echo [3/7] qidong FastAPI fuwu (duankou 8000)...
start "FastAPI Server" cmd /k "cd /d D:\bishe_zoujun\fastapi && uvicorn main:app --reload"
timeout /t 3 >nul

echo [4/7] qidong Nginx fanxiang daili (duankou 80)...
start "Nginx Proxy" cmd /k "D:\app\nginx\nginx-1.30.0\nginx.exe -p D:\app\nginx\nginx-1.30.0"
timeout /t 3 >nul

echo [5/7] qidong nginx-exporter (duankou 9113)...
start "Nginx Exporter" cmd /k "D:\app\nginx-exporter\nginx-prometheus-exporter.exe -nginx.scrape-uri http://localhost:80/nginx_status"
timeout /t 3 >nul

echo [6/7] qidong Prometheus (duankou 9090)...
start "Prometheus" cmd /k "cd /d D:\app\permetheus\prometheus-3.4.0.windows-amd64 && prometheus.exe --config.file=prometheus.yml"
timeout /t 3 >nul

echo [7/7] qidong Grafana (duankou 3001)...
start "Grafana" cmd /k "D:\app\grafana\grafana-13.0.1+security-01\bin\grafana.exe server -config D:\app\grafana\grafana-13.0.1+security-01\conf\defaults.ini"
timeout /t 3 >nul

@REM .\start_all.bat
echo.
echo ========================================
echo suoyou fuwu yijing qidong
echo ========================================
echo.
echo fangwen dizhi (tongguo Nginx, duankou 80):
echo   - dasha:     http://localhost/demo.html
echo   - denglu:    http://localhost/login.html
echo   - houtai:    http://localhost/admin.html
echo   - pinggu:    http://localhost/analyst.html
echo   - API:       http://localhost/api/docs
echo   - Node.js:   http://localhost:3000 (zhijie fangwen)
echo   - FastAPI:   http://localhost:8000/docs (zhijie fangwen)
echo.
echo moren zhanghao:
echo   - guanliyuan: admin3 / 123456
echo   - putong yonghu: user1 / 123456
echo.
echo Nginx tingzhi: nginx -s stop
echo.
pause
