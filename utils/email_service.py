from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives


def send_otp(email: str, otp_code: str, purpose: str, expires_in: int):
    subject = "Your ReferralPro OTP Code"
    from_email = settings.DEFAULT_FROM_EMAIL

    # Render HTML template
    html_content = render_to_string('OTP.html', {
        'otp': otp_code,
        'purpose': purpose,
        'expires_in': expires_in
    })

    # Also make a plain-text fallback (for clients that can’t render HTML)
    text_content = f"Your OTP for {purpose} is {otp_code}. It will expire in {expires_in} minutes."

    msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    print("OTP email sent.")




def send_invitation_email(email: str, name: str, password: str):
    subject = "You're invited to join ReferralPro"
    from_email = settings.DEFAULT_FROM_EMAIL

    # Render HTML template (create `invitation.html` in templates folder)
    html_content = render_to_string('invitation.html', {
        'name': name,
        'email': email,
        'password': password,
    })

    # Plain text fallback
    text_content = f"""
    Hi {name},

    You’ve been invited to join ReferralPro as an employee.

    Here are your login credentials:
    Email: {email}
    Password: {password}

    Please log in and update your password after your first login.

    Regards,
    ReferralPro Team
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    print(f"Invitation email sent to {email}")




