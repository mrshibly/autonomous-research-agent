"""
FastAPI application entry point.

Autonomous AI Research Agent — Backend API
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.utils.websocket_manager import manager

from app.config import get_settings
from app.database import init_db
from app.routers.research import router as research_router
from app.utils.security import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    logger.info("🚀 Starting Autonomous AI Research Agent...")

    # Initialize database tables
    await init_db()
    logger.info("✅ Database initialized.")

    settings = get_settings()
    logger.info(f"📡 LLM Provider: {settings.llm_provider}")
    logger.info(f"🔍 Search Provider: {settings.search_provider}")
    logger.info(f"📊 Embedding Provider: {settings.embedding_provider}")

    yield

    logger.info("🛑 Shutting down...")


# ── App Creation ──────────────────────────────────────────────────

settings = get_settings()

app = FastAPI(
    title="Autonomous AI Research Agent",
    description=(
        "An AI-powered research assistant that searches the web, "
        "reads papers, summarizes findings, and generates structured "
        "research reports with citations."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ────────────────────────────────────────────────────

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# ── Routers ───────────────────────────────────────────────────────
 
app.include_router(research_router, prefix="/api/v1")
 
# ── Static Files (Frontend) ───────────────────────────────────────
 
# If running in production/docker, serve the built frontend
# We look for the dist folder in a few possible relative locations
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if not os.path.exists(frontend_dist):
    # Fallback for alternative structures
    frontend_dist = "/app/frontend/dist"

if os.path.exists(frontend_dist):
    logger.info(f"🌐 Serving frontend from {frontend_dist}")
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    logger.warning("⚠️ Frontend dist folder not found. API-only mode.")


# ── Health Check ──────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Autonomous AI Research Agent",
        "version": "1.0.0",
        "llm_provider": settings.llm_provider,
        "search_provider": settings.search_provider,
    }


# ── Global Exception Handler ─────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return a clean error response."""
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred.",
            "error_code": "INTERNAL_ERROR",
        },
    )

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time research task updates.
    Clients subscribe to updates for a specific task_id.
    """
    await manager.connect(websocket, task_id)
    try:
        while True:
            # Keep connection alive, though we mostly push updates to the client
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
        manager.disconnect(websocket, task_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
