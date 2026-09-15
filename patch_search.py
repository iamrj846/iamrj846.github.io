import re

with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/services/search_service.py', 'r') as f:
    content = f.read()

patch_code = '''
        import time
        from app.services.metrics_service import get_metrics_service
        metrics_svc = get_metrics_service()

        redis_start = time.time()
        matching_hashes = set()
        all_keys = client.keys("*|*")
        metrics_svc.record_redis_latency((time.time() - redis_start) * 1000)
'''

content = content.replace(
    '        matching_hashes = set()\n        all_keys = client.keys("*|*")',
    patch_code
)

with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/services/search_service.py', 'w') as f:
    f.write(content)
print("Patched search_service.py")
