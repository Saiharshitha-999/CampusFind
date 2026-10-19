from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router
from pathlib import Path
from fastapi.staticfiles import StaticFiles
import logging

app = FastAPI(title=settings.app_name, version="0.1.0")
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount('/uploads', StaticFiles(directory=settings.upload_dir), name='uploads')
logger = logging.getLogger('campusfind')

@app.middleware('http')
async def log_unhandled_errors(request, call_next):
    try:
        return await call_next(request)
    except Exception:
        logger.exception('Unhandled request error: %s %s', request.method, request.url.path)
        raise
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)

@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
