import os
import time
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
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
    
    # Pre-populate initial jobs in background to guarantee immediate server responsiveness
    ingestion_mgr = get_ingestion_manager()
    asyncio.create_task(asyncio.to_thread(ingestion_mgr.seed_initial_jobs))
    
    # Start 30-minute recurring scheduler if enabled
    enable_scheduler = os.getenv("ENABLE_INGESTION_SCHEDULER", "true").lower() in ("1", "true", "yes")
    if enable_scheduler:
        ingestion_mgr.start_scheduler()
    else:
        logger.info("Background ingestion scheduler disabled on this node (ENABLE_INGESTION_SCHEDULER=false)")
    
    from app.services.metrics_service import get_metrics_service
    get_metrics_service().start_flusher()
    logger.info("CorporateGuild server ready.")
    
    yield
    
    # Shutdown tasks
    if enable_scheduler:
        logger.info("Shutting down background scheduler...")
        ingestion_mgr.stop_scheduler()
    get_metrics_service().stop_flusher()

config = get_config()

app = FastAPI(
    title=config.app_name,
    description="Production Job Search Portal & Career Network API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS

from app.services.metrics_service import get_metrics_service
import time

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    if request.url.path == "/api/jobs/search":
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        metrics = get_metrics_service()
        # metrics.increment_search()
        metrics.record_search_latency(duration_ms)
        return response
    elif request.url.path == "/api/jobs/click":
        metrics = get_metrics_service()
        # metrics.increment_click()
        return await call_next(request)
    else:
        return await call_next(request)

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

# No-Cache headers for dynamic application HTML files
NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0"
}

def serve_html(path_obj):
    return FileResponse(str(path_obj), headers=NO_CACHE_HEADERS)

# Clean Page Routes (Served from frontend/)
@app.api_route("/", methods=["GET", "HEAD"])
@app.api_route("/home", methods=["GET", "HEAD"])
@app.api_route("/index.html", methods=["GET", "HEAD"])
async def serve_home(request: Request):
    # Check for legacy query parameters that caused GSC redirect issues
    qp = request.query_params
    role = (qp.get("role") or "").strip().lower()
    loc = (qp.get("location") or "").strip().lower()
    
    role_to_page = {
        "software engineer": "/jobs/software-engineer.html",
        "frontend developer": "/jobs/frontend-developer.html",
        "frontend engineer": "/jobs/frontend-developer.html",
        "backend developer": "/jobs/backend-developer.html",
        "backend engineer": "/jobs/backend-developer.html",
        "full stack developer": "/jobs/full-stack-developer.html",
        "full stack engineer": "/jobs/full-stack-developer.html",
        "data engineer": "/jobs/data-engineer.html",
        "data scientist": "/jobs/data-scientist.html",
        "product manager": "/jobs/product-manager.html",
        "devops engineer": "/jobs/devops-engineer.html",
        "cloud engineer": "/jobs/cloud-engineer.html",
        "ui/ux designer": "/jobs/ui-ux-designer.html",
        "machine learning engineer": "/jobs/machine-learning-engineer.html",
        "cybersecurity engineer": "/jobs/cybersecurity-engineer.html",
        "software engineer india": "/jobs/software-engineer-india.html",
        "entry level software engineer": "/jobs/entry-level-software-engineer.html",
        "remote software engineer": "/jobs/remote-software-engineer.html",
    }
    
    if role and role in role_to_page and not loc:
        return RedirectResponse(url=role_to_page[role], status_code=301)
    
    if role or loc:
        return RedirectResponse(url=f"/jobs.html?{request.url.query}", status_code=301)

    # Primary landing is the Job Search Portal
    return serve_html(FRONTEND_DIR / "index.html")

@app.api_route("/favicon.ico", methods=["GET", "HEAD"])
async def serve_favicon():
    if (STATIC_DIR / "favicon.ico").exists():
        return FileResponse(str(STATIC_DIR / "favicon.ico"))
    return FileResponse(str(STATIC_DIR / "logo.png"))

@app.api_route("/jobs", methods=["GET", "HEAD"])
@app.api_route("/jobs.html", methods=["GET", "HEAD"])
async def serve_jobs():
    return serve_html(FRONTEND_DIR / "jobs.html")

@app.api_route("/jobs/{slug}", methods=["GET", "HEAD"])
async def serve_article(slug: str):
    path = FRONTEND_DIR / "jobs" / slug
    if path.exists() and path.is_file():
        return serve_html(path)
    if not slug.endswith(".html"):
        path_html = FRONTEND_DIR / "jobs" / f"{slug}.html"
        if path_html.exists() and path_html.is_file():
            return serve_html(path_html)
    raise HTTPException(status_code=404, detail="Not Found")

@app.api_route("/portfolio", methods=["GET", "HEAD"])
@app.api_route("/portfolio.html", methods=["GET", "HEAD"])
async def serve_portfolio():
    return serve_html(FRONTEND_DIR / "portfolio.html")

@app.api_route("/articles", methods=["GET", "HEAD"])
@app.api_route("/articles.html", methods=["GET", "HEAD"])
async def serve_articles():
    return serve_html(FRONTEND_DIR / "articles.html")

@app.api_route("/contact", methods=["GET", "HEAD"])
@app.api_route("/contact.html", methods=["GET", "HEAD"])
async def serve_contact():
    return serve_html(FRONTEND_DIR / "contact.html")

@app.api_route("/privacy", methods=["GET", "HEAD"])
@app.api_route("/privacy.html", methods=["GET", "HEAD"])
async def serve_privacy():
    return serve_html(FRONTEND_DIR / "privacy.html")

@app.api_route("/disclaimer", methods=["GET", "HEAD"])
@app.api_route("/disclaimer.html", methods=["GET", "HEAD"])
async def serve_disclaimer():
    return serve_html(FRONTEND_DIR / "disclaimer.html")

@app.api_route("/admin", methods=["GET", "HEAD"])
@app.api_route("/admin.html", methods=["GET", "HEAD"])
@app.api_route(config.admin_dashboard_url, methods=["GET", "HEAD"])
async def serve_admin():
    return serve_html(FRONTEND_DIR / "admin.html")

# Static & SEO files transparent root fallbacks (Served from frontend/static/)
@app.api_route("/logo.png", methods=["GET", "HEAD"])
async def serve_logo():
    return FileResponse(str(STATIC_DIR / "logo.png"))

@app.api_route("/robots.txt", methods=["GET", "HEAD"])
async def serve_robots():
    return FileResponse(str(STATIC_DIR / "robots.txt"), media_type="text/plain; charset=utf-8")

@app.api_route("/sitemap.xml", methods=["GET", "HEAD"])
async def serve_sitemap():
    return FileResponse(str(STATIC_DIR / "sitemap.xml"), media_type="application/xml; charset=utf-8")

@app.api_route("/manifest.json", methods=["GET", "HEAD"])
async def serve_manifest():
    return FileResponse(str(STATIC_DIR / "manifest.json"), media_type="application/manifest+json; charset=utf-8")

@app.api_route("/schema.json", methods=["GET", "HEAD"])
async def serve_schema():
    return FileResponse(str(STATIC_DIR / "schema.json"), media_type="application/ld+json; charset=utf-8")

@app.api_route("/humans.txt", methods=["GET", "HEAD"])
async def serve_humans():
    return FileResponse(str(STATIC_DIR / "humans.txt"), media_type="text/plain; charset=utf-8")

@app.api_route("/.well-known/security.txt", methods=["GET", "HEAD"])
@app.api_route("/security.txt", methods=["GET", "HEAD"])
async def serve_security():
    return FileResponse(str(STATIC_DIR / "security.txt"), media_type="text/plain; charset=utf-8")

@app.api_route("/health", methods=["GET", "HEAD"])
@app.api_route("/api/health", methods=["GET", "HEAD"])
async def health_check():
    return {"status": "ok", "service": "corporateguild", "version": "1.0.0"}

@app.api_route("/llms.txt", methods=["GET", "HEAD"])
async def serve_llms():
    return FileResponse(str(STATIC_DIR / "llms.txt"), media_type="text/markdown; charset=utf-8")

@app.api_route("/llms-full.txt", methods=["GET", "HEAD"])
async def serve_llms_full():
    return FileResponse(str(STATIC_DIR / "llms-full.txt"), media_type="text/markdown; charset=utf-8")

@app.api_route("/telemetry.js", methods=["GET", "HEAD"])
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
