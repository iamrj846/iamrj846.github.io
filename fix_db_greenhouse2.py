import sqlite3

def fix_db():
    conn = sqlite3.connect('/Users/iamrj846/Desktop/iamrj846.github.io/data/jobs_portal.db')
    cur = conn.cursor()
    cur.execute("SELECT id, apply_url FROM jobs WHERE apply_url LIKE '%api%'")
    rows = cur.fetchall()
    count = 0
    
    for r in rows:
        job_id, url = r
        if 'api.greenhouse' in url or 'boards-api' in url:
            new_url = url.replace('boards-api.greenhouse.io/v1/boards', 'boards.greenhouse.io')
            new_url = new_url.replace('api.greenhouse.io', 'boards.greenhouse.io')
            cur.execute("UPDATE jobs SET apply_url = ? WHERE id = ?", (new_url, job_id))
            count += 1
            
    conn.commit()
    conn.close()
    print(f"Fixed {count} DB entries.")

fix_db()
