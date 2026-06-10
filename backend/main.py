from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import asyncio

# 🌟 Core fix: Windows Playwright compatibility
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.api import chat, homework, auth
from app.auth.store import UserStore
from app.services.screenshot_service import cleanup_browser


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init user DB, shutdown: cleanup browser + http clients."""
    # Initialize SQLite user store with default accounts
    store = UserStore()
    await store.init_db()
    print("✅ User database initialized with default accounts")

    yield

    # Shutdown cleanup
    cleanup_browser()
    print("🧹 Browser and services cleaned up")


app = FastAPI(title="AI Assistant Backend", lifespan=lifespan)

# Restrict CORS to known frontend origin (localhost:5173 in dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(homework.router, prefix="/api/homework", tags=["Homework"])


@app.get("/")
async def root():
    return {"message": "AI Assistant API is running. Homework pipeline ready!"}
