from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import asyncio

# 🌟 核心修复 1：解决 Windows 下 Playwright 运行报错 NotImplementedError 的问题
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# 引入我们的路由文件
from app.api import chat
from app.api import homework

# 这就是 Uvicorn 在苦苦寻找的 "app" 变量！
app = FastAPI(title="AI Assistant Backend")

# 配置 CORS，允许前端 Vue 跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源（本地开发环境）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 将路由挂载到主程序上
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(homework.router, prefix="/api/homework", tags=["Homework"])

# 根目录健康检查
@app.get("/")
async def root():
    return {"message": "AI Assistant API is running. Homework pipeline ready!"}