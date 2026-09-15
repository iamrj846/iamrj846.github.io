import sqlite3
from app.redis_client import get_redis_client

def fix_db():
    conn = sqlite3.connect('/Users/iamrj846/Desktop/iamrj846.github.io/data/jobs_portal.db')
    cur = conn.cursor()
    cur.execute("SELECT id, apply_url FROM jobs WHERE apply_url LIKE '%api%'")
    rows = cur.fetchall()
    
    r_client = get_redis_client()
    count = 0
    
    for r in rows:
        job_id, url = r
        if 'api.greenhouse' in url or 'boards-api' in url:
            new_url = url.replace('boards-api.greenhouse.io/v1/boards', 'boards.greenhouse.io')
            new_url = new_url.replace('api.greenhouse.io', 'boards.greenhouse.io')
            cur.execute("UPDATE jobs SET apply_url = ? WHERE id = ?", (new_url, job_id))
            count += 1
            
            # Update Redis
            keys = r_client.keys("*|*")
            for k in keys:
                hdata = r_client.hgetall(k)
                if url in hdata:
                    val = hdata[url]
                    r_client.hdel(k, url)
                    r_client.hset(k, new_url, val)

    conn.commit()
    conn.close()
    print(f"Fixed {count} DB entries.")

fix_db()
