import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.config import get_config

logger = logging.getLogger("email_service")

def build_otp_html(otp: str, user_name: str = "") -> str:
    name_salutation = f"Hi {user_name}," if user_name else "Hello,"
    return f"""<!DOCTYPE html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="color-scheme" content="light dark">
  <meta name="supported-color-schemes" content="light dark">
  <title>Your Verification Code: {otp}</title>
  <!--[if mso]>
  <noscript>
    <xml>
      <o:OfficeDocumentSettings>
        <o:PixelsPerInch>96</o:PixelsPerInch>
      </o:OfficeDocumentSettings>
    </xml>
  </noscript>
  <![endif]-->
  <style>
    :root {{
      color-scheme: light dark;
      supported-color-schemes: light dark;
    }}
    body, table, td, div, p, a {{
      -webkit-text-size-adjust: 100%;
      -ms-text-size-adjust: 100%;
    }}
    /* Dark Mode Media Query for Apple Mail, iOS Mail, Outlook */
    @media (prefers-color-scheme: dark) {{
      body, .email-bg {{
        background-color: #0b0f19 !important;
      }}
      .email-card {{
        background-color: #111827 !important;
        border-color: #1f2937 !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6) !important;
      }}
      .brand-title {{
        color: #f9fafb !important;
      }}
      .brand-accent {{
        color: #818cf8 !important;
      }}
      .brand-subtitle {{
        color: #9ca3af !important;
      }}
      .email-salutation {{
        color: #f3f4f6 !important;
      }}
      .email-body-text {{
        color: #d1d5db !important;
      }}
      .otp-container {{
        background-color: #1e1b4b !important;
        border-color: #6366f1 !important;
      }}
      .otp-label {{
        color: #a5b4fc !important;
      }}
      .otp-pill {{
        background-color: #4f46e5 !important;
        color: #ffffff !important;
      }}
      .otp-expiry {{
        color: #9ca3af !important;
      }}
      .email-notice {{
        color: #6b7280 !important;
      }}
      .email-footer {{
        background-color: #070a10 !important;
        border-color: #1f2937 !important;
        color: #6b7280 !important;
      }}
    }}
    /* Gmail Android/iOS App Dark Mode Overrides */
    [data-ogsc] .email-bg {{ background-color: #0b0f19 !important; }}
    [data-ogsc] .email-card {{ background-color: #111827 !important; border-color: #1f2937 !important; }}
    [data-ogsc] .brand-title {{ color: #f9fafb !important; }}
    [data-ogsc] .brand-accent {{ color: #818cf8 !important; }}
    [data-ogsc] .brand-subtitle {{ color: #9ca3af !important; }}
    [data-ogsc] .email-salutation {{ color: #f3f4f6 !important; }}
    [data-ogsc] .email-body-text {{ color: #d1d5db !important; }}
    [data-ogsc] .otp-container {{ background-color: #1e1b4b !important; border-color: #6366f1 !important; }}
    [data-ogsc] .otp-label {{ color: #a5b4fc !important; }}
    [data-ogsc] .otp-pill {{ background-color: #4f46e5 !important; color: #ffffff !important; }}
    [data-ogsc] .otp-expiry {{ color: #9ca3af !important; }}
    [data-ogsc] .email-footer {{ background-color: #070a10 !important; color: #6b7280 !important; }}
  </style>
</head>
<body style="margin:0; padding:0; background-color:#f1f5f9; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing:antialiased;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" class="email-bg" style="background-color:#f1f5f9; padding:40px 12px;">
    <tr>
      <td align="center">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" class="email-card" style="max-width:520px; background-color:#ffffff; border-radius:18px; border:1px solid #e2e8f0; overflow:hidden; box-shadow:0 8px 30px rgba(15,23,42,0.08);">
          
          <!-- Header Branding -->
          <tr>
            <td align="center" style="padding:32px 24px 20px; text-align:center;">
              <div style="display:inline-block; margin-bottom:12px;">
                <img src="https://corporateguild.com/static/logo.png" alt="CorporateGuild Logo" width="52" height="52" style="display:inline-block; width:52px; height:52px; border-radius:14px; vertical-align:middle; box-shadow:0 4px 12px rgba(79,70,229,0.25); object-fit:contain;" />
              </div>
              <div class="brand-title" style="font-size:24px; font-weight:850; letter-spacing:-0.5px; color:#0f172a; line-height:1.2;">
                <span class="brand-accent" style="color:#4f46e5; font-weight:900;">Corporate</span>Guild
              </div>
              <div class="brand-subtitle" style="font-size:12.5px; color:#64748b; font-weight:600; margin-top:4px; letter-spacing:0.3px;">
                Verified Careers &bull; ATS Direct Feed
              </div>
            </td>
          </tr>

          <!-- Main Content -->
          <tr>
            <td style="padding:0 32px 28px;">
              <h1 class="email-salutation" style="font-size:18px; font-weight:750; color:#0f172a; margin:0 0 12px; line-height:1.4;">
                {name_salutation}
              </h1>
              <p class="email-body-text" style="font-size:14.5px; color:#334155; line-height:1.6; margin:0 0 24px;">
                Thank you for signing up for free unlimited access to all jobs. Please use the 6-digit verification code below to activate your account and unlock unlimited job search access:
              </p>

              <!-- High Contrast OTP Section -->
              <table width="100%" border="0" cellspacing="0" cellpadding="0" class="otp-container" style="background-color:#eef2ff; border:2px dashed #818cf8; border-radius:14px; margin:24px 0;">
                <tr>
                  <td align="center" style="padding:22px 16px;">
                    <div class="otp-label" style="font-size:11px; text-transform:uppercase; color:#4f46e5; letter-spacing:2px; font-weight:800; margin-bottom:12px;">
                      Your Verification Code
                    </div>
                    
                    <!-- Solid High-Contrast Digits Badge -->
                    <div class="otp-pill" style="display:inline-block; background-color:#4f46e5; color:#ffffff; font-size:32px; font-weight:900; letter-spacing:8px; padding:12px 26px; border-radius:12px; font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; text-align:center; box-shadow:0 4px 14px rgba(79,70,229,0.35);">
                      {otp}
                    </div>

                    <div class="otp-expiry" style="font-size:12px; color:#64748b; font-weight:600; margin-top:12px;">
                      Valid for <strong>15 minutes</strong> &bull; Do not share with anyone
                    </div>
                  </td>
                </tr>
              </table>

              <p class="email-notice" style="font-size:12.5px; color:#64748b; line-height:1.5; margin:20px 0 0;">
                🔒 If you did not request this code, you can safely disregard this email. Your email address cannot be registered without this verification code.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td align="center" class="email-footer" style="padding:18px 24px; background-color:#f8fafc; border-top:1px solid #e2e8f0; text-align:center;">
              <div style="font-size:11.5px; color:#94a3b8; line-height:1.5;">
                &copy; 2026 CorporateGuild &bull; Real-time India ATS Portal
                <br>
                Official Verification Dispatch Service
              </div>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

def build_otp_plain(otp: str, user_name: str = "") -> str:
    salutation = f"Hi {user_name}," if user_name else "Hello,"
    return f"""{salutation}

Thank you for signing up for free unlimited access to all jobs. Please use the 6-digit verification code below to activate your account and unlock unlimited job search access:

{otp}

This code is valid for 15 minutes. Enter this code on the verification screen to activate your unlimited search access.

If you did not request this code, you can safely ignore this email.

Best regards,
CorporateGuild Team
"""

def send_otp_email(to_email: str, otp: str, user_name: str = "") -> bool:
    """
    Sends an OTP verification email to to_email using the configured SMTP server.
    Returns True if successfully dispatched, False otherwise.
    """
    config = get_config()
    smtp_user = config.smtp_user
    smtp_pass = config.smtp_password
    smtp_host = config.smtp_host
    smtp_port = config.smtp_port
    from_email = config.smtp_from_email
    use_tls = config.smtp_use_tls

    if not smtp_user or not smtp_pass:
        logger.error(
            f"SMTP credentials not configured (user='{smtp_user}'). "
            f"Live email cannot be dispatched to {to_email}."
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your CorporateGuild Verification Code: {otp}"
        msg["From"] = from_email
        msg["To"] = to_email

        plain_text = build_otp_plain(otp, user_name)
        html_text = build_otp_html(otp, user_name)

        msg.attach(MIMEText(plain_text, "plain", "utf-8"))
        msg.attach(MIMEText(html_text, "html", "utf-8"))

        clean_pass = smtp_pass.strip()
        ports_to_try = [smtp_port]
        fallback_port = 465 if smtp_port != 465 else 587
        if fallback_port not in ports_to_try:
            ports_to_try.append(fallback_port)

        last_error = None
        for port in ports_to_try:
            try:
                if port == 465:
                    with smtplib.SMTP_SSL(smtp_host, port, timeout=12.0) as server:
                        try:
                            server.login(smtp_user, clean_pass)
                        except Exception:
                            server.login(smtp_user, clean_pass.replace(" ", ""))
                        server.sendmail(from_email, [to_email], msg.as_string())
                else:
                    with smtplib.SMTP(smtp_host, port, timeout=12.0) as server:
                        if use_tls:
                            server.starttls()
                        try:
                            server.login(smtp_user, clean_pass)
                        except Exception:
                            server.login(smtp_user, clean_pass.replace(" ", ""))
                        server.sendmail(from_email, [to_email], msg.as_string())

                logger.info(f"Successfully sent verification OTP email to {to_email} via {smtp_host}:{port}")
                return True
            except Exception as port_err:
                last_error = port_err
                logger.warning(f"SMTP dispatch on {smtp_host}:{port} failed: {port_err}. Trying alternate port...")

        if last_error:
            logger.error(f"Failed to dispatch OTP email to {to_email} via SMTP after trying ports {ports_to_try}: {last_error}")
        return False

    except Exception as e:
        logger.error(f"Failed to dispatch OTP email to {to_email} via SMTP: {e}")
        return False
