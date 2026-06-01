@echo off
:: 设置控制台为 UTF-8 编码，防止中文乱码
chcp 65001 >nul

echo ===================================================
echo     🚀 AI 智能教务工作台 - 极速本地启动向导
echo ===================================================
echo.

:: 1. 启动后端
echo [1/3] 正在检查/安装 Python 依赖并启动后端服务...
cd backend
call pip install -r requirements.txt
:: 自动下载 Playwright 需要的 Chromium 浏览器内核
call playwright install chromium

:: 弹出一个新的黑框专门运行 FastAPI 后端
start "AI Backend (FastAPI)" cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000"
cd ..

echo.
:: 2. 启动前端
echo [2/3] 正在检查/安装 Node.js 依赖并启动前端服务...
cd frontend
call npm install

:: 弹出一个新的黑框专门运行 Vue 前端
start "AI Frontend (Vue3)" cmd /k "npm run dev"
cd ..

echo.
:: 3. 等待服务就绪并打开浏览器
echo [3/3] 服务拉起中，请勿关闭弹出的黑框，稍后自动为您打开浏览器...
:: 等待 4 秒给前后端启动的时间
timeout /t 4 /nobreak >nul

:: 调用系统默认浏览器打开前端页面
start http://localhost:5173

echo.
echo ✅ 全部启动成功！如需停止服务，直接关闭两个弹出的黑框即可。
pause