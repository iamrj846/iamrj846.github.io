import re

with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/routers/jobs.py', 'r') as f:
    content = f.read()

patch_code = '''
    # Record search telemetry in SQLite
    q_str = (custom_input or search_term or role or "").strip()
    import time
    from app.services.metrics_service import get_metrics_service
    db_start = time.time()
    record_site_search(session_token, ip, query=q_str, page_path="/")
    get_metrics_service().record_db_latency((time.time() - db_start) * 1000)
'''

content = content.replace(
    '    # Record search telemetry in SQLite\n    q_str = (custom_input or search_term or role or "").strip()\n    record_site_search(session_token, ip, query=q_str, page_path="/")',
    patch_code
)

with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/routers/jobs.py', 'w') as f:
    f.write(content)
print("Patched jobs.py")
