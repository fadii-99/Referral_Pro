from django.core.mail import send_mail
from django.conf import settings

def send_otp(email: str, otp_code: str):
    subject = "Your ReferralPro OTP Code"
    message = f"Your OTP code is {otp_code}. It will expire in 3 minutes."
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [email], fail_silently=False)

def send_password_reset(email: str, reset_link: str):
    subject = "ReferralPro Password Reset"
    message = f"Click the link to reset your password: {reset_link}"
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [email], fail_silently=False)
