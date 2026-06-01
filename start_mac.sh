#!/bin/bash

echo "==================================================="
echo "    🚀 AI 智能教务工作台 - 极速本地启动向导"
echo "==================================================="
echo ""

# 1. 启动后端 (放入后台运行)
echo "[1/3] 正在检查/安装 Python 依赖并启动后端服务..."
cd backend
pip3 install -r requirements.txt
playwright install chromium
# 后台启动 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

echo ""
# 2. 启动前端 (放入后台运行)
echo "[2/3] 正在检查/安装 Node.js 依赖并启动前端服务..."
cd frontend
npm install
# 后台启动 vite
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
# 3. 等待服务就绪并自动打开浏览器
echo "[3/3] 服务拉起中，稍后自动为您打开浏览器..."
sleep 4

# 智能判断系统环境并打开浏览器
if which xdg-open > /dev/null
then
  xdg-open http://localhost:5173
elif which open > /dev/null
then
  open http://localhost:5173
fi

echo ""
echo "✅ 全部启动成功！请保留此终端窗口运行。"
echo "🛑 如需退出并关闭所有服务，请在此窗口按 Ctrl + C"

# 优雅退出：捕获 Ctrl+C，同时杀掉后端和前端进程
trap "echo -e '\n正在关闭教务工作台服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait