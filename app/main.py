import os
import time
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_config, BASE_DIR, FRONTEND_DIR, STATIC_DIR
from app.database import init_db
from app.redis_client import get_redis_client
from app.services.ingestion_service import get_ingestion_manager
from app.routers import jobs, auth, admin, telemetry, contact

# Setup logging
log_handlers = [logging.StreamHandler()]
log_dir = "/app/logs" if os.path.exists("/app/logs") else "logs"
try:
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")
    log_handlers.append(
        RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
    )
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=log_handlers
)
logger = logging.getLogger("server")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    logger.info("Initializing CorporateGuild backend services...")
    init_db()
    get_redis_client()
    
    # Pre-populate initial jobs
    ingestion_mgr = get_ingestion_manager()
    ingestion_mgr.seed_initial_jobs()
    
    # Start 30-minute recurring scheduler
    ingestion_mgr.start_scheduler()
    logger.info("CorporateGuild server ready.")
    
    yield
    
    # Shutdown tasks
    logger.info("Shutting down background scheduler...")
    ingestion_mgr.stop_scheduler()

config = get_config()

app = FastAPI(
    title=config.app_name,
    description="Production India Job Search Portal & Career Network API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(jobs.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(telemetry.router)
app.include_router(contact.router)

# Mount Static Files directory
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Clean Page Routes (Served from frontend/)
@app.get("/")
@app.get("/home")
@app.get("/index.html")
async def serve_home():
    # Primary landing is the Job Search Portal
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/favicon.ico")
async def serve_favicon():
    if (STATIC_DIR / "favicon.ico").exists():
        return FileResponse(str(STATIC_DIR / "favicon.ico"))
    return FileResponse(str(STATIC_DIR / "logo.png"))

@app.get("/jobs")
@app.get("/jobs.html")
async def serve_jobs():
    return FileResponse(str(FRONTEND_DIR / "jobs.html"))

@app.get("/portfolio")
@app.get("/portfolio.html")
async def serve_portfolio():
    return FileResponse(str(FRONTEND_DIR / "portfolio.html"))

@app.get("/contact")
@app.get("/contact.html")
async def serve_contact():
    return FileResponse(str(FRONTEND_DIR / "contact.html"))

@app.get("/privacy")
@app.get("/privacy.html")
async def serve_privacy():
    return FileResponse(str(FRONTEND_DIR / "privacy.html"))

@app.get("/disclaimer")
@app.get("/disclaimer.html")
async def serve_disclaimer():
    return FileResponse(str(FRONTEND_DIR / "disclaimer.html"))

@app.get("/admin")
@app.get("/admin.html")
@app.get(config.admin_dashboard_url)
async def serve_admin():
    return FileResponse(str(FRONTEND_DIR / "admin.html"))

# Static & SEO files transparent root fallbacks (Served from frontend/static/)
@app.get("/logo.png")
async def serve_logo():
    return FileResponse(str(STATIC_DIR / "logo.png"))

@app.get("/robots.txt")
async def serve_robots():
    return FileResponse(str(STATIC_DIR / "robots.txt"), media_type="text/plain; charset=utf-8")

@app.get("/sitemap.xml")
async def serve_sitemap():
    return FileResponse(str(STATIC_DIR / "sitemap.xml"), media_type="application/xml; charset=utf-8")

@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse(str(STATIC_DIR / "manifest.json"), media_type="application/manifest+json; charset=utf-8")

@app.get("/schema.json")
async def serve_schema():
    return FileResponse(str(STATIC_DIR / "schema.json"), media_type="application/ld+json; charset=utf-8")

@app.get("/humans.txt")
async def serve_humans():
    return FileResponse(str(STATIC_DIR / "humans.txt"), media_type="text/plain; charset=utf-8")

@app.get("/.well-known/security.txt")
@app.get("/security.txt")
async def serve_security():
    return FileResponse(str(STATIC_DIR / "security.txt"), media_type="text/plain; charset=utf-8")

@app.get("/telemetry.js")
async def serve_telemetry():
    return FileResponse(str(STATIC_DIR / "telemetry.js"), media_type="application/javascript; charset=utf-8")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error. Please retry shortly."}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=config.host, port=config.port, reload=config.debug)
