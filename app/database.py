import sqlite3
import datetime
import pytz
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import bcrypt

from app.config import get_config

logger = logging.getLogger("database")

def get_ist_now() -> datetime.datetime:
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.datetime.now(tz)

def get_ist_now_str() -> str:
    return get_ist_now().strftime("%Y-%m-%d %H:%M:%S IST")

def get_db_connection() -> sqlite3.Connection:
    config = get_config()
    db_path = config.db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        otp_code TEXT,
        otp_expiry TEXT,
        is_verified INTEGER DEFAULT 0,
        created_at TEXT,
        last_login TEXT,
        total_visits INTEGER DEFAULT 1,
        total_clicks INTEGER DEFAULT 0,
        total_searches INTEGER DEFAULT 0,
        session_token TEXT,
        session_active INTEGER DEFAULT 1,
        is_admin INTEGER DEFAULT 0,
        ip_address TEXT,
        metadata TEXT
    )
    """)

    # Jobs table for persistent SQLite storage
    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT NOT NULL,
        role_category TEXT,
        workplace_type TEXT,
        salary_range TEXT,
        experience_level TEXT,
        source TEXT,
        tags TEXT,
        skills TEXT,
        description TEXT,
        apply_url TEXT,
        is_active INTEGER DEFAULT 1,
        posted_at TEXT,
        updated_at TEXT
    )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_role ON jobs(role_category);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_loc ON jobs(location);")

    # Site telemetry table (capturing visits, clicks on links/buttons, searches)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS site_telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        ip_address TEXT,
        user_id INTEGER,
        event_type TEXT,
        target_element TEXT,
        target_label TEXT,
        page_path TEXT,
        timestamp TEXT
    )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_telem_session ON site_telemetry(session_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_telem_event ON site_telemetry(event_type);")

    # Guest quota tracking (by persistent guest_id cookie and fallback IP)
    cur.execute("PRAGMA table_info(guest_quotas);")
    cols = cur.fetchall()
    if cols:
        ip_pk = any(c["name"] == "ip_address" and c["pk"] == 1 for c in cols)
        if ip_pk:
            cur.execute("""
            CREATE TABLE guest_quotas_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guest_id TEXT,
                ip_address TEXT,
                search_count INTEGER DEFAULT 0,
                last_search_at TEXT,
                created_at TEXT
            )
            """)
            has_guest_id = any(c["name"] == "guest_id" for c in cols)
            if has_guest_id:
                cur.execute("INSERT INTO guest_quotas_new (guest_id, ip_address, search_count, last_search_at, created_at) SELECT guest_id, ip_address, search_count, last_search_at, created_at FROM guest_quotas;")
            else:
                cur.execute("INSERT INTO guest_quotas_new (ip_address, search_count, last_search_at, created_at) SELECT ip_address, search_count, last_search_at, created_at FROM guest_quotas;")
            cur.execute("DROP TABLE guest_quotas;")
            cur.execute("ALTER TABLE guest_quotas_new RENAME TO guest_quotas;")
    else:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS guest_quotas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_id TEXT,
            ip_address TEXT,
            search_count INTEGER DEFAULT 0,
            last_search_at TEXT,
            created_at TEXT
        )
        """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_guest_quotas_guest_id ON guest_quotas(guest_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_guest_quotas_ip ON guest_quotas(ip_address);")

    # Contact messages table for persistent message storage & admin review
    cur.execute("""
    CREATE TABLE IF NOT EXISTS contact_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        subject TEXT,
        message TEXT NOT NULL,
        created_at_ist TEXT NOT NULL,
        ip_address TEXT,
        status TEXT DEFAULT 'unread'
    )
    """)

    # Activity logs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        ip_address TEXT,
        action TEXT,
        details TEXT,
        timestamp TEXT
    )
    """)
    conn.commit()

    # Seed admin user if not exists (with both jainraunak846@gmail.com and iamrj846)
    config = get_config()
    # Admin sessions table for cross-process multi-worker session validity
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin_sessions (
        token TEXT PRIMARY KEY,
        admin_email TEXT,
        created_at TEXT
    )
    """)

    try:
        cur.execute("ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0;")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN otp_code TEXT;")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN otp_expiry TEXT;")
    except Exception:
        pass

    # Migrate legacy click telemetry: separate genuine job apply clicks from generic UI clicks
    try:
        cur.execute("UPDATE site_telemetry SET event_type = 'job_click' WHERE event_type = 'click' AND target_element = 'job_apply_btn';")
        cur.execute("UPDATE site_telemetry SET event_type = 'ui_click' WHERE event_type = 'click' AND target_element != 'job_apply_btn';")
        cur.execute("""
        UPDATE users SET total_clicks = COALESCE(
            (SELECT COUNT(*) FROM site_telemetry WHERE site_telemetry.user_id = users.id AND site_telemetry.event_type = 'job_click'),
            0
        );
        """)
        conn.commit()
    except Exception:
        pass

    # Admin Account Seeding
    admin_user = config.admin_username
    admin_pass = config.admin_password_fallback
    admin_email = "jainraunak846@gmail.com"
    cur.execute("SELECT id FROM users WHERE LOWER(email) IN (?, ?) OR name = ?", (admin_email, f"{admin_user}@corporateguild.com", admin_user))
    row = cur.fetchone()
    now_str = get_ist_now_str()
    if not row:
        pw_hash = bcrypt.hashpw(admin_pass.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cur.execute("""
        INSERT INTO users (name, email, password_hash, is_verified, created_at, last_login, is_admin, total_visits, total_clicks, is_blocked)
        VALUES (?, ?, ?, 1, ?, ?, 1, 1, 0, 0)
        """, (admin_user, admin_email, pw_hash, now_str, now_str))
        conn.commit()
        logger.info(f"Initialized admin user: {admin_user} ({admin_email})")
    else:
        # Ensure email is updated to jainraunak846@gmail.com
        cur.execute("UPDATE users SET email = ?, is_admin = 1, is_blocked = 0 WHERE id = ?", (admin_email, row["id"]))
        conn.commit()

    conn.close()

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_session(session_token: str) -> Optional[Dict[str, Any]]:
    if not session_token:
        return None
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE session_token = ? AND session_active = 1 AND (is_blocked IS NULL OR is_blocked = 0)", (session_token,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(name: str, email: str, password_hash: str, otp_code: str, otp_expiry: str, ip_address: str = "") -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    now_str = get_ist_now_str()
    cur.execute("""
    INSERT INTO users (name, email, password_hash, otp_code, otp_expiry, is_verified, created_at, last_login, ip_address)
    VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
    """, (name, email.strip().lower(), password_hash, otp_code, otp_expiry, now_str, now_str, ip_address))
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id

def verify_user_otp(email: str, otp_code: str, session_token: str) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    now = get_ist_now()
    cur.execute("SELECT id, otp_code, otp_expiry FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    user_id, stored_otp, expiry_str = row["id"], row["otp_code"], row["otp_expiry"]
    if stored_otp != otp_code.strip():
        conn.close()
        return False
    # Check expiry if formatted
    if expiry_str:
        try:
            exp_dt = datetime.datetime.fromisoformat(expiry_str)
            if now > exp_dt:
                conn.close()
                return False
        except Exception:
            pass
    now_str = get_ist_now_str()
    cur.execute("""
    UPDATE users 
    SET is_verified = 1, otp_code = NULL, session_token = ?, session_active = 1, last_login = ?
    WHERE id = ?
    """, (session_token, now_str, user_id))
    conn.commit()
    conn.close()
    return True

def set_user_otp(email: str, otp_code: str, otp_expiry: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET otp_code = ?, otp_expiry = ? WHERE LOWER(email) = LOWER(?)", (otp_code, otp_expiry, email.strip()))
    conn.commit()
    conn.close()

def update_user_login(user_id: int, session_token: str, ip_address: str = ""):
    conn = get_db_connection()
    cur = conn.cursor()
    now_str = get_ist_now_str()
    cur.execute("""
    UPDATE users 
    SET session_token = ?, session_active = 1, last_login = ?, total_visits = total_visits + 1, ip_address = ?
    WHERE id = ?
    """, (session_token, now_str, ip_address, user_id))
    conn.commit()
    conn.close()

def logout_user(session_token: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET session_active = 0, session_token = NULL WHERE session_token = ?", (session_token,))
    conn.commit()
    conn.close()

def increment_user_metric(user_id: int, metric: str):
    if metric not in ("total_searches", "total_clicks", "total_visits"):
        return
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE users SET {metric} = {metric} + 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_guest_search_count(ip_address: str, guest_id: Optional[str] = None) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    # Check by persistent guest_id cookie first
    if guest_id:
        cur.execute("SELECT search_count FROM guest_quotas WHERE guest_id = ?", (guest_id,))
        row = cur.fetchone()
        conn.close()
        return int(row["search_count"]) if row else 0
    # Fallback to IP address if guest_id is absent
    cur.execute("SELECT search_count FROM guest_quotas WHERE ip_address = ?", (ip_address,))
    row = cur.fetchone()
    conn.close()
    return int(row["search_count"]) if row else 0

def increment_guest_search(ip_address: str, guest_id: Optional[str] = None) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    now_str = get_ist_now_str()
    row = None
    if guest_id:
        cur.execute("SELECT search_count, ip_address FROM guest_quotas WHERE guest_id = ?", (guest_id,))
        row = cur.fetchone()
    else:
        cur.execute("SELECT search_count, guest_id FROM guest_quotas WHERE ip_address = ?", (ip_address,))
        row = cur.fetchone()

    if row:
        new_count = row["search_count"] + 1
        if guest_id:
            cur.execute(
                "UPDATE guest_quotas SET search_count = ?, last_search_at = ?, ip_address = ? WHERE guest_id = ?",
                (new_count, now_str, ip_address, guest_id)
            )
        else:
            cur.execute(
                "UPDATE guest_quotas SET search_count = ?, last_search_at = ? WHERE ip_address = ?",
                (new_count, now_str, ip_address)
            )
    else:
        new_count = 1
        cur.execute(
            "INSERT INTO guest_quotas (ip_address, guest_id, search_count, last_search_at, created_at) VALUES (?, ?, 1, ?, ?)",
            (ip_address, guest_id or "", now_str, now_str)
        )
    conn.commit()
    conn.close()
    return new_count

def save_contact_message(name: str, email: str, subject: str, message: str, ip_address: str = "") -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    now_str = get_ist_now_str()
    cur.execute("""
    INSERT INTO contact_messages (name, email, subject, message, created_at_ist, ip_address, status)
    VALUES (?, ?, ?, ?, ?, ?, 'unread')
    """, (name, email, subject, message, now_str, ip_address))
    conn.commit()
    msg_id = cur.lastrowid
    conn.close()
    return msg_id

def get_contact_messages(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM contact_messages ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def log_activity(user_id: Optional[int], ip_address: str, action: str, details: str = ""):
    conn = get_db_connection()
    cur = conn.cursor()
    now_str = get_ist_now_str()
    cur.execute("""
    INSERT INTO user_activity_logs (user_id, ip_address, action, details, timestamp)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, ip_address, action, details, now_str))
    conn.commit()
    conn.close()

def save_jobs_to_db(jobs_list: List[Dict[str, Any]]) -> int:
    if not jobs_list:
        return 0
    conn = get_db_connection()
    cur = conn.cursor()
    count = 0
    now_str = get_ist_now_str()
    for j in jobs_list:
        c_name = j.get("company_name") or j.get("company", "Tech Enterprise")
        r_name = j.get("role_name") or j.get("title", "Software Engineer")
        p_time = j.get("posted_timestamp_ist") or j.get("posted_at") or now_str
        job_id = j.get("id") or f"{c_name}_{r_name}_{p_time}"
        job_id = "".join([c if c.isalnum() or c in ('_', '-') else '_' for c in str(job_id)])[:120]
        
        tags_val = j.get("tags", [])
        tags_json = json.dumps(tags_val) if isinstance(tags_val, (list, dict)) else str(tags_val)
        skills_val = j.get("skills", [])
        skills_json = json.dumps(skills_val) if isinstance(skills_val, (list, dict)) else str(skills_val)
        
        cur.execute("""
        INSERT INTO jobs (
            id, title, company, location, role_category, workplace_type, 
            salary_range, experience_level, source, tags, skills, 
            description, apply_url, is_active, posted_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            company = excluded.company,
            location = excluded.location,
            role_category = excluded.role_category,
            workplace_type = excluded.workplace_type,
            salary_range = excluded.salary_range,
            experience_level = excluded.experience_level,
            source = excluded.source,
            tags = excluded.tags,
            skills = excluded.skills,
            description = excluded.description,
            apply_url = excluded.apply_url,
            is_active = 1,
            updated_at = excluded.updated_at
        """, (
            job_id,
            r_name,
            c_name,
            j.get("location", "Bengaluru, Karnataka, India"),
            j.get("role_category") or r_name,
            j.get("workplace_type", "In office"),
            j.get("salary_range", "Competitive Market CTC"),
            j.get("experience_level", "Senior"),
            j.get("ats_platform") or j.get("source", "Direct"),
            tags_json,
            skills_json,
            j.get("description", ""),
            j.get("apply_link") or j.get("apply_url", "https://corporateguild.com"),
            p_time,
            now_str
        ))
        count += 1
    conn.commit()
    conn.close()
    return count

def get_total_jobs_in_db() -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM jobs WHERE is_active = 1")
    count = cur.fetchone()[0]
    conn.close()
    return count

def record_site_visit(session_token: Optional[str], ip_address: str, page_path: str = "/"):
    conn = get_db_connection()
    cur = conn.cursor()
    now_str = get_ist_now_str()
    user_id = None
    if session_token:
        cur.execute("SELECT id FROM users WHERE session_token = ?", (session_token,))
        row = cur.fetchone()
        if row:
            user_id = row["id"]
            cur.execute("UPDATE users SET total_visits = total_visits + 1, last_login = ?, ip_address = ? WHERE id = ?", (now_str, ip_address, user_id))
    cur.execute("""
    INSERT INTO site_telemetry (session_id, ip_address, user_id, event_type, target_element, target_label, page_path, timestamp)
    VALUES (?, ?, ?, 'visit', 'window', 'page_load', ?, ?)
    """, (session_token or 'guest_session', ip_address, user_id, page_path, now_str))
    conn.commit()
    conn.close()

def record_site_click(session_token: Optional[str], ip_address: str, target_element: str, target_label: str = "", page_path: str = "/"):
    conn = get_db_connection()
    cur = conn.cursor()
    now_str = get_ist_now_str()
    user_id = None
    if session_token:
        cur.execute("SELECT id FROM users WHERE session_token = ?", (session_token,))
        row = cur.fetchone()
        if row:
            user_id = row["id"]
    # Generic UI clicks (navigation, tabs, dropdowns) are recorded as 'ui_click' and DO NOT increment user job apply metrics
    cur.execute("""
    INSERT INTO site_telemetry (session_id, ip_address, user_id, event_type, target_element, target_label, page_path, timestamp)
    VALUES (?, ?, ?, 'ui_click', ?, ?, ?, ?)
    """, (session_token or 'guest_session', ip_address, user_id, target_element, target_label, page_path, now_str))
    conn.commit()
    conn.close()

def record_job_apply_click(session_token: Optional[str], ip_address: str, company_name: str, role_name: str, apply_link: str = "", page_path: str = "/"):
    conn = get_db_connection()
    cur = conn.cursor()
    now_str = get_ist_now_str()
    user_id = None
    if session_token:
        cur.execute("SELECT id FROM users WHERE session_token = ?", (session_token,))
        row = cur.fetchone()
        if row:
            user_id = row["id"]
            cur.execute("UPDATE users SET total_clicks = total_clicks + 1 WHERE id = ?", (user_id,))
    cur.execute("""
    INSERT INTO site_telemetry (session_id, ip_address, user_id, event_type, target_element, target_label, page_path, timestamp)
    VALUES (?, ?, ?, 'job_click', 'job_apply_btn', ?, ?, ?)
    """, (session_token or 'guest_session', ip_address, user_id, f"{company_name} - {role_name}", page_path, now_str))
    conn.commit()
    conn.close()

def record_site_search(session_token: Optional[str], ip_address: str, query: str = "", page_path: str = "/"):
    conn = get_db_connection()
    cur = conn.cursor()
    now_str = get_ist_now_str()
    user_id = None
    if session_token:
        cur.execute("SELECT id FROM users WHERE session_token = ?", (session_token,))
        row = cur.fetchone()
        if row:
            user_id = row["id"]
    cur.execute("""
    INSERT INTO site_telemetry (session_id, ip_address, user_id, event_type, target_element, target_label, page_path, timestamp)
    VALUES (?, ?, ?, 'search', 'search_input', ?, ?, ?)
    """, (session_token or 'guest_session', ip_address, user_id, query, page_path, now_str))
    conn.commit()
    conn.close()

def get_admin_metrics() -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE session_active = 1")
    active_sessions = cur.fetchone()[0]

    # Only actual job direct apply clicks are counted in total_clicks
    cur.execute("SELECT COUNT(*) FROM site_telemetry WHERE event_type = 'job_click'")
    telem_clicks = cur.fetchone()[0] or 0
    cur.execute("SELECT SUM(total_clicks) FROM users")
    u_clicks = cur.fetchone()[0] or 0
    total_clicks = max(telem_clicks, u_clicks)

    cur.execute("SELECT COUNT(*) FROM site_telemetry WHERE event_type = 'search'")
    telem_searches = cur.fetchone()[0]
    cur.execute("SELECT SUM(total_searches) FROM users")
    u_searches = cur.fetchone()[0] or 0
    cur.execute("SELECT SUM(search_count), COUNT(*) FROM guest_quotas")
    g_searches, g_visitors = cur.fetchone()
    g_searches = g_searches or 0
    g_visitors = g_visitors or 0
    total_searches = max(telem_searches, u_searches + g_searches)

    cur.execute("SELECT COUNT(*) FROM site_telemetry WHERE event_type = 'visit'")
    telem_visits = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT session_id) FROM site_telemetry WHERE event_type = 'visit'")
    unique_visit_sessions = cur.fetchone()[0]
    cur.execute("SELECT SUM(total_visits) FROM users")
    u_visits = cur.fetchone()[0] or 0
    total_visits = max(telem_visits, u_visits + g_visitors, unique_visit_sessions)

    cur.execute("SELECT COUNT(*) FROM jobs WHERE is_active = 1")
    total_jobs_in_db = cur.fetchone()[0]

    conn.close()
    return {
        "total_users": total_users,
        "active_sessions": active_sessions,
        "total_searches": total_searches,
        "total_clicks": total_clicks,
        "total_visits": total_visits,
        "guest_visitors": g_visitors,
        "guest_searches": g_searches,
        "total_jobs_in_db": total_jobs_in_db
    }

def get_all_users() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, name, email, is_verified, is_admin, total_visits, total_clicks, total_searches, 
           session_active, last_login, created_at, ip_address, COALESCE(is_blocked, 0) as is_blocked,
           otp_code
    FROM users 
    ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_admin_session(token: str, admin_email: str) -> None:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin_sessions (
        token TEXT PRIMARY KEY,
        admin_email TEXT,
        created_at TEXT
    )
    """)
    now_str = get_ist_now_str()
    cur.execute("INSERT OR REPLACE INTO admin_sessions (token, admin_email, created_at) VALUES (?, ?, ?)", (token, admin_email, now_str))
    # Also update admin user row in users table
    cur.execute("UPDATE users SET session_token = ?, session_active = 1, last_login = ? WHERE is_admin = 1", (token, now_str))
    conn.commit()
    conn.close()

def delete_admin_session(token: str) -> bool:
    if not token:
        return False
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin_sessions (
        token TEXT PRIMARY KEY,
        admin_email TEXT,
        created_at TEXT
    )
    """)
    cur.execute("DELETE FROM admin_sessions WHERE token = ?", (token,))
    cur.execute("UPDATE users SET session_active = 0, session_token = NULL WHERE session_token = ? AND is_admin = 1", (token,))
    conn.commit()
    conn.close()
    return True

def is_valid_admin_session(token: str) -> bool:
    if not token:
        return False
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin_sessions (
        token TEXT PRIMARY KEY,
        admin_email TEXT,
        created_at TEXT
    )
    """)
    cur.execute("SELECT token FROM admin_sessions WHERE token = ?", (token,))
    if cur.fetchone():
        conn.close()
        return True
    cur.execute("SELECT id FROM users WHERE session_token = ? AND session_active = 1 AND is_admin = 1", (token,))
    row = cur.fetchone()
    conn.close()
    return bool(row)

def block_user(user_id: int, block: bool = True) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    val = 1 if block else 0
    cur.execute("UPDATE users SET is_blocked = ?, session_active = ? WHERE id = ? AND is_admin = 0", (val, 0 if block else 1, user_id))
    success = cur.rowcount > 0
    conn.commit()
    conn.close()
    return success

def delete_user(user_id: int) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM user_activity_logs WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM users WHERE id = ? AND is_admin = 0", (user_id,))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def admin_create_user(name: str, email: str, password_hash: str, is_admin: bool = False, is_blocked: bool = False) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    now_str = get_ist_now_str()
    cur.execute("""
    INSERT INTO users (name, email, password_hash, is_admin, is_verified, is_blocked, session_active, created_at, last_login)
    VALUES (?, ?, ?, ?, 1, ?, 0, ?, ?)
    """, (name.strip(), email.strip().lower(), password_hash, 1 if is_admin else 0, 1 if is_blocked else 0, now_str, now_str))
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id

def verify_user_manually(user_id: int) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = 1 WHERE id = ?", (user_id,))
    success = cur.rowcount > 0
    conn.commit()
    conn.close()
    return success

def update_contact_status(contact_id: int, status: str) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE contact_messages SET status = ? WHERE id = ?", (status.strip().lower(), contact_id))
    success = cur.rowcount > 0
    conn.commit()
    conn.close()
    return success

