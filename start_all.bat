@echo off
chcp 65001 >nul
echo ========================================
echo dianying shuju fenxi xitong - yijian qidong
echo ========================================
echo.

echo [1/3] qidong Node.js fuwu (duankou 3000)...
start "Node.js Server" cmd /k "cd /d D:\bishe_zoujun\Web_Node && node app.js"
timeout /t 3 >nul

echo [2/3] qidong Flask fuwu (duankou 5000)...
start "Flask Server" cmd /k "cd /d D:\bishe_zoujun\Flask && python app2.py"
timeout /t 3 >nul

echo [3/3] qidong FastAPI fuwu (duankou 8000)...
start "FastAPI Server" cmd /k "cd /d D:\bishe_zoujun\fastapi && uvicorn app3:app --reload"

echo.
echo ========================================
echo suoyou fuwu yijing qidong
echo ========================================
echo.
echo fangwen dizhi:
echo   - dasha: http://localhost:3000/demo.html
echo   - denglu: http://localhost:3000/login.html
echo   - houtai: http://localhost:3000/admin.html
echo   - API: http://localhost:8000/docs
echo.
echo moren zhanghao:
echo   - guanliyuan: admin3 / 123456
echo   - putong yonghu: user1 / 123456
echo.
pause
