import logging
import httpx
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.config import get_config
from app.database import save_contact_message

logger = logging.getLogger("contact_router")
router = APIRouter(prefix="/api/contact", tags=["Contact"])

class ContactRequest(BaseModel):
    name: str
    email: str
    subject: Optional[str] = "General Inquiry"
    message: str

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

async def forward_email_via_formsubmit(name: str, email: str, subject: str, message: str):
    """
    Forwards contact form inquiry via FormSubmit API token configured in .env.
    """
    config = get_config()
    form_token = config.formsubmit_token.strip()
    if not form_token:
        logger.info("FORMSUBMIT_TOKEN not configured in environment. Inquiry recorded in database.")
        return

    payload = {
        "_subject": f"[CorporateGuild Contact] {subject or 'New Inquiry'} from {name}",
        "name": name,
        "email": email,
        "message": message,
        "_template": "table",
        "_captcha": "false"
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(f"https://formsubmit.co/ajax/{form_token}", json=payload)
            logger.info(f"FormSubmit email dispatch status: {resp.status_code}")
    except Exception as e:
        logger.warning(f"FormSubmit email dispatch background task notice: {e}")

@router.post("")
@router.post("/")
async def submit_contact_form(request: Request, payload: ContactRequest, bg_tasks: BackgroundTasks):
    name = payload.name.strip()
    email = payload.email.strip().lower()
    message = payload.message.strip()
    subject = (payload.subject or "CorporateGuild Inquiry").strip()

    if not name or not email or not message:
        raise HTTPException(status_code=400, detail="Name, email, and message are required.")

    ip = get_client_ip(request)

    # 1. Permanently record message in SQLite database (so no inquiry is ever lost)
    try:
        msg_id = save_contact_message(name, email, subject, message, ip)
        logger.info(f"Saved contact inquiry #{msg_id} from {email}")
    except Exception as e:
        logger.error(f"Failed to save contact message to database: {e}")

    # 2. Dispatch email delivery via FormSubmit token in background
    bg_tasks.add_task(forward_email_via_formsubmit, name, email, subject, message)

    return {
        "success": True,
        "message": "Thank you! Your message has been sent directly to our team. We will get back to you shortly."
    }
