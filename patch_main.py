import re

with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/main.py', 'r') as f:
    content = f.read()

middleware_code = '''
from app.services.metrics_service import get_metrics_service
import time

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    if request.url.path == "/api/jobs/search":
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        metrics = get_metrics_service()
        metrics.increment_search()
        metrics.record_search_latency(duration_ms)
        return response
    elif request.url.path == "/api/jobs/click":
        metrics = get_metrics_service()
        metrics.increment_click()
        return await call_next(request)
    else:
        return await call_next(request)
'''

# insert middleware after app = FastAPI(...)
if '@app.middleware("http")' not in content:
    content = content.replace(
        'app.add_middleware(\n    CORSMiddleware,',
        middleware_code + '\napp.add_middleware(\n    CORSMiddleware,'
    )

# Start/stop flusher in lifespan
lifespan_old = '''    # Start 30-minute recurring scheduler
    ingestion_mgr.start_scheduler()
    logger.info("CorporateGuild server ready.")'''

lifespan_new = '''    # Start 30-minute recurring scheduler
    ingestion_mgr.start_scheduler()
    
    from app.services.metrics_service import get_metrics_service
    get_metrics_service().start_flusher()
    logger.info("CorporateGuild server ready.")'''

content = content.replace(lifespan_old, lifespan_new)

lifespan_old_down = '''    # Shutdown tasks
    logger.info("Shutting down background scheduler...")
    ingestion_mgr.stop_scheduler()'''
    
lifespan_new_down = '''    # Shutdown tasks
    logger.info("Shutting down background scheduler...")
    ingestion_mgr.stop_scheduler()
    get_metrics_service().stop_flusher()'''
    
content = content.replace(lifespan_old_down, lifespan_new_down)

with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/main.py', 'w') as f:
    f.write(content)

print("Patched main.py")
