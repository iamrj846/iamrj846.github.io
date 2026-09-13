import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"

def load_dotenv_file():
    # Priority:
    # 1. Detect target environment (APP_ENV, ENVIRONMENT, or ENV)
    env_mode = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", os.getenv("ENV", "local"))).lower().strip()
    
    candidate_files = []
    if env_mode in ("prod", "production"):
        candidate_files = [BASE_DIR / ".env.prod", BASE_DIR / ".env.production", BASE_DIR / ".env"]
    else:
        candidate_files = [BASE_DIR / ".env.local", BASE_DIR / ".env"]

    loaded_keys = set()
    for env_file in candidate_files:
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            if k and k not in os.environ and k not in loaded_keys:
                                os.environ[k] = v
                                loaded_keys.add(k)
            except Exception:
                pass

load_dotenv_file()

def load_yaml_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    if not config_path:
        config_path = os.getenv("CONFIG_PATH", str(BASE_DIR / "application.yml"))
    path = Path(config_path)
    if not path.is_absolute():
        path = BASE_DIR / path
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

class Config:
    def __init__(self, raw: Optional[Dict[str, Any]] = None):
        self._raw = raw or load_yaml_config()
        self.app = self._raw.get("app", {})
        self.resources = self._raw.get("resources", {})
        self.redis = self._raw.get("redis", {})
        self.database = self._raw.get("database", {})
        self.admin = self._raw.get("admin", {})
        self.scheduler = self._raw.get("scheduler", {})
        self.guest = self._raw.get("guest", {})

    @property
    def app_name(self) -> str:
        return self.app.get("name", "CorporateGuild Job Search Portal")

    @property
    def host(self) -> str:
        return self.app.get("host", "0.0.0.0")

    @property
    def port(self) -> int:
        return int(self.app.get("port", 8000))

    @property
    def debug(self) -> bool:
        return bool(self.app.get("debug", True))

    @property
    def timezone_str(self) -> str:
        return self.app.get("timezone", "Asia/Kolkata")

    @property
    def cookie_secret(self) -> str:
        return os.getenv("COOKIE_SECRET", self.app.get("cookie_secret", "corporateguild-secret-2026"))

    @property
    def secret_key(self) -> str:
        return os.getenv("SECRET_KEY", "corporateguild-jwt-secret-ist-2026")

    @property
    def excel_path(self) -> Path:
        rel = os.getenv("EXCEL_PATH", self.resources.get("excel_path", "resources/job_urls.xlsx"))
        p = Path(rel)
        return p if p.is_absolute() else (BASE_DIR / p)

    @property
    def redis_host(self) -> str:
        return os.getenv("REDIS_HOST", self.redis.get("host", "127.0.0.1"))

    @property
    def redis_port(self) -> int:
        return int(os.getenv("REDIS_PORT", self.redis.get("port", 6379)))

    @property
    def redis_db(self) -> int:
        return int(os.getenv("REDIS_DB", self.redis.get("db", 0)))

    @property
    def redis_password(self) -> Optional[str]:
        p = os.getenv("REDIS_PASSWORD", self.redis.get("password", None))
        return str(p) if p else None

    @property
    def redis_ttl_seconds(self) -> int:
        return int(os.getenv("REDIS_TTL_SECONDS", self.redis.get("ttl_seconds", 604800))) # 7 days

    @property
    def db_path(self) -> Path:
        rel = os.getenv("DATABASE_PATH", self.database.get("path", "data/jobs_portal.db"))
        p = Path(rel)
        return p if p.is_absolute() else (BASE_DIR / p)

    @property
    def admin_username(self) -> str:
        return os.getenv("ADMIN_USERNAME", self.admin.get("username", "iamrj846"))

    @property
    def admin_password_fallback(self) -> str:
        return os.getenv("ADMIN_PASSWORD", self.admin.get("plain_password_fallback", "iamrj846"))

    @property
    def admin_dashboard_url(self) -> str:
        return self.admin.get("dashboard_url", "/admin-dashboard")

    @property
    def free_search_limit(self) -> int:
        return int(os.getenv("FREE_SEARCH_LIMIT", self.guest.get("free_search_limit", 5)))

    @property
    def sync_interval_minutes(self) -> int:
        return int(os.getenv("SYNC_INTERVAL_MINUTES", self.scheduler.get("sync_interval_minutes", 10)))

_config_instance: Optional[Config] = None

def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
