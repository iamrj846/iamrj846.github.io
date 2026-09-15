from app.services.email_service import send_otp_email
success = send_otp_email("jainraunak846@gmail.com", "123456", "Test User")
print("Success:", success)
