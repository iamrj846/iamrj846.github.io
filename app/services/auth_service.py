import secrets
import random
import logging
import datetime
import pytz
from typing import Dict, Any, Optional, Tuple
import bcrypt

from app.config import get_config
from app.database import (
    get_user_by_email, get_user_by_session, create_user, verify_user_otp,
    set_user_otp, update_user_login, logout_user, increment_user_metric,
    get_guest_search_count, increment_guest_search, log_activity, get_ist_now
)

logger = logging.getLogger("auth_service")
IST_TZ = pytz.timezone("Asia/Kolkata")

class AuthService:
    def __init__(self):
        self.config = get_config()

    def generate_otp(self) -> str:
        return f"{random.randint(100000, 999999)}"

    def check_search_allowed(self, ip_address: str, session_token: Optional[str], guest_id: Optional[str] = None, increment: bool = True) -> Dict[str, Any]:
        """
        Validates if search is permitted:
        - Authenticated users: UNLIMITED
        - Guests: maximum 5 searches tracked per persistent guest cookie and fallback IP.
          Only decrements when increment=True (i.e. user explicitly clicked Search or Apply Filters).
        """
        user = get_user_by_session(session_token) if session_token else None
        if user and user.get("is_verified", 0) == 1:
            if increment:
                increment_user_metric(user["id"], "total_searches")
                log_activity(user["id"], ip_address, "search", "authenticated search")
            return {
                "allowed": True,
                "remaining": 99999,
                "is_authenticated": True,
                "user": {"name": user["name"], "email": user["email"]}
            }

        # Guest mode (tracked by persistent guest device cookie + IP fallback)
        current_searches = get_guest_search_count(ip_address, guest_id)
        limit = self.config.free_search_limit

        if current_searches >= limit:
            return {
                "allowed": False,
                "remaining": 0,
                "is_authenticated": False,
                "current_count": current_searches,
                "limit": limit,
                "message": f"You have reached your {limit} free searches. Please sign up or log in to unlock unlimited searches."
            }

        if not increment:
            # Read-only check (e.g. initial page load, feed browsing, pagination)
            remaining = max(0, limit - current_searches)
            return {
                "allowed": True,
                "remaining": remaining,
                "is_authenticated": False,
                "current_count": current_searches,
                "limit": limit
            }

        # Allow search & increment count on intentional search or filter action
        new_count = increment_guest_search(ip_address, guest_id)
        remaining = max(0, limit - new_count)
        log_activity(None, ip_address, "search", f"guest search #{new_count} (device: {guest_id or ip_address})")
        return {
            "allowed": True,
            "remaining": remaining,
            "is_authenticated": False,
            "current_count": new_count,
            "limit": limit
        }

    def register_user(self, name: str, email: str, password: str, ip_address: str = "") -> Dict[str, Any]:
        email = email.strip().lower()
        if not email or "@" not in email:
            return {"success": False, "message": "Invalid email address format."}
        if len(password) < 6:
            return {"success": False, "message": "Password must be at least 6 characters."}

        existing = get_user_by_email(email)
        otp = self.generate_otp()
        expiry = (get_ist_now() + datetime.timedelta(minutes=15)).isoformat()
        user_name = name or email.split("@")[0]

        from app.services.email_service import send_otp_email

        if existing:
            if existing.get("is_verified", 0) == 1:
                return {"success": False, "message": "An account with this email already exists. Please log in."}
            else:
                # Update OTP for unverified existing account
                set_user_otp(email, otp, expiry)
                logger.info(f"Generated fresh OTP for unverified user {email}")
                send_otp_email(email, otp, existing.get("name") or user_name)
                return {
                    "success": True,
                    "message": "Verification code sent to your email. Please check your inbox."
                }

        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        create_user(user_name, email, pw_hash, otp, expiry, ip_address)
        log_activity(None, ip_address, "signup_init", f"Registered {email}")
        logger.info(f"Signup initiated for {email}")
        send_otp_email(email, otp, user_name)

        return {
            "success": True,
            "message": "Verification code sent to your email. Please enter the 6-digit code to complete registration."
        }

    def resend_otp(self, email: str, ip_address: str = "") -> Dict[str, Any]:
        email = email.strip().lower()
        user = get_user_by_email(email)
        if not user:
            return {"success": False, "message": "No account found with this email address."}
        if user.get("is_verified", 0) == 1:
            return {"success": False, "message": "This account is already verified. Please log in."}

        otp = self.generate_otp()
        expiry = (get_ist_now() + datetime.timedelta(minutes=15)).isoformat()
        set_user_otp(email, otp, expiry)

        from app.services.email_service import send_otp_email
        send_otp_email(email, otp, user.get("name", ""))
        log_activity(user["id"], ip_address, "otp_resend", f"Resent OTP for {email}")
        logger.info(f"Resent OTP for {email}")

        return {
            "success": True,
            "message": "A fresh 6-digit verification code has been sent to your email."
        }

    def verify_otp(self, email: str, otp: str, ip_address: str = "") -> Dict[str, Any]:
        email = email.strip().lower()
        session_token = secrets.token_urlsafe(32)
        ok = verify_user_otp(email, otp, session_token)
        if not ok:
            return {"success": False, "message": "Invalid or expired OTP code."}

        user = get_user_by_email(email)
        log_activity(user["id"] if user else None, ip_address, "login_otp", f"OTP verified for {email}")
        return {
            "success": True,
            "message": "Account verified and logged in successfully!",
            "session_token": session_token,
            "user": {
                "name": user["name"] if user else email,
                "email": email,
                "is_admin": bool(user.get("is_admin", 0)) if user else False
            }
        }

    def login_with_password(self, email: str, password: str, ip_address: str = "") -> Dict[str, Any]:
        email = email.strip().lower()
        user = get_user_by_email(email)
        if not user:
            from app.database import get_db_connection
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE LOWER(name) = ? OR LOWER(email) = ?", (email, email))
            row = cur.fetchone()
            conn.close()
            if row:
                user = dict(row)

        if not user:
            return {"success": False, "message": "Invalid email or password."}

        if user.get("is_blocked", 0) == 1:
            return {"success": False, "message": "This account has been suspended. Please contact support."}

        # Check password
        try:
            pw_ok = bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8"))
        except Exception:
            pw_ok = False

        if not pw_ok:
            # Fallback for plain admin password in config
            if (email.startswith(self.config.admin_username) or email in ("jainraunak846@gmail.com", f"{self.config.admin_username}@corporateguild.com")) and password == self.config.admin_password_fallback:
                pw_ok = True

        if not pw_ok:
            return {"success": False, "message": "Invalid email or password."}

        session_token = secrets.token_urlsafe(32)
        update_user_login(user["id"], session_token, ip_address)
        log_activity(user["id"], ip_address, "login_pwd", f"Logged in: {email}")

        return {
            "success": True,
            "message": "Logged in successfully!",
            "session_token": session_token,
            "user": {
                "name": user["name"],
                "email": user["email"],
                "is_admin": bool(user.get("is_admin", 0))
            }
        }

    def logout(self, session_token: str):
        logout_user(session_token)

    def record_job_click(self, ip_address: str, session_token: Optional[str], job_details: Dict[str, Any]):
        user = get_user_by_session(session_token) if session_token else None
        if user:
            log_activity(user["id"], ip_address, "job_apply", f"Applied: {job_details.get('company_name')} - {job_details.get('role_name')}")
        else:
            log_activity(None, ip_address, "job_apply", f"Guest Applied: {job_details.get('company_name')} - {job_details.get('role_name')}")

_auth_service: Optional[AuthService] = None

def get_auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
