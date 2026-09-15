import re

with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/routers/admin.py', 'r') as f:
    content = f.read()

metrics_route = '''
@router.get("/system_metrics")
async def get_system_metrics(request: Request, hours: int = 1):
    verify_admin_session(request)
    from app.services.metrics_service import get_metrics_service
    metrics_svc = get_metrics_service()
    data = metrics_svc.get_metrics(hours=hours)
    return {"success": True, "metrics": data}
'''

if '@router.get("/system_metrics")' not in content:
    content = content.replace('def verify_admin_session(request: Request)', metrics_route + '\ndef verify_admin_session(request: Request)')

with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/routers/admin.py', 'w') as f:
    f.write(content)
print("Added route to admin.py")
