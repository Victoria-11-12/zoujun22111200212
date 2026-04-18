@echo off
chcp 65001 >nul
echo ========================================
echo 电影数据分析系统 - 一键启动脚本
echo ========================================
echo.

echo [1/3] 启动 Node.js 服务 (端口 3000)...
start "Node.js Server" cmd /k "cd /d %~dp0..\Web_Node && node app.js"
timeout /t 3 >nul

echo [2/3] 启动 Flask 服务 (端口 5000)...
start "Flask Server" cmd /k "cd /d %~dp0..\Flask && python app2.py"
timeout /t 3 >nul

echo [3/3] 启动 FastAPI 服务 (端口 8000)...
start "FastAPI Server" cmd /k "cd /d %~dp0..\fastapi && uvicorn app3:app --reload"

echo.
echo ========================================
echo 所有服务启动完成！
echo ========================================
echo.
echo 访问地址:
echo   - 数据大屏: http://localhost:3000/demo.html
echo   - 登录页面: http://localhost:3000/login.html
echo   - 后台管理: http://localhost:3000/admin.html
echo   - API文档:  http://localhost:8000/docs
echo.
echo 默认账号:
echo   - 管理员: admin3 / 123456
echo   - 普通用户: user1 / 123456
echo.
pause
