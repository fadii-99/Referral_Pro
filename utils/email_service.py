from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives


support_url = "https://thereferralpro.com/contact"

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

    You've been invited to join ReferralPro as an employee.

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


def send_app_download_email(email: str, name: str,  sender_name: str = None):
    subject = "Join ReferralPro - Download the App & Register Your Company"
    from_email = settings.DEFAULT_FROM_EMAIL

    # Render HTML template
    html_content = render_to_string('app_download_invitation.html', {
        'name': name,
        'email': email,
        'sender_name': sender_name,
        'website_url': 'https://thereferralpro.com/',
    })

    # Plain text fallback
    text_content = f"""
    Hi {name},

    {'You have been invited by ' + sender_name + ' to' if sender_name else 'You are invited to'} join ReferralPro - the ultimate referral platform for businesses!

    "Register your companyand start building your referral network today.

    🚀 What you can do with ReferralPro:
    • Build and manage your referral network
    • Track referral performance and results  
    • Connect with trusted business partners
    • Grow your business through quality referrals

    📱 Get Started:
    1. Visit: https://thereferralpro.com/
    2. Register your company
    3. Start building your referral network

    Don't miss out on the opportunity to grow your business through the power of referrals!

    Best regards,
    The ReferralPro Team
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    print(f"App download invitation email sent to {email}")


def send_solo_signup_success_email(email: str, name: str):
    subject = "Welcome to ReferralPro!"
    from_email = settings.DEFAULT_FROM_EMAIL

    html_content = render_to_string('solo_signup_success.html', {
        'name': name,
        'email': email,
        'login_url': 'https://thereferralpro.com/login',
    })

    text_content = f"""
    Hi {name},

    Your ReferralPro account has been created successfully!

    You can log in now using your email: {email}.
    Visit: https://thereferralpro.com/login

    Welcome aboard!
    - ReferralPro Team
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    print(f"Solo signup success email sent to {email}")


def send_company_signup_email(email: str, name: str):
    subject = "Welcome to ReferralPro for Business"
    from_email = settings.DEFAULT_FROM_EMAIL

    html_content = render_to_string('company_signup.html', {
        'name': name,
        'email': email,
        'dashboard_url': 'https://thereferralpro.com',
    })

    text_content = f"""
    Hi {name},

    Your company account has been successfully created on ReferralPro.

    Visit your dashboard: https://thereferralpro.com

    Regards,
    ReferralPro Team
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    print(f"Company signup email sent to {email}")



def send_payment_success_email(email: str, name: str, plan_name: str, amount: float, currency: str, expiry_date, receipt_url: str):
    subject = "Your Subscription Payment was Successful"
    from_email = settings.DEFAULT_FROM_EMAIL

    html_content = render_to_string('payment_success.html', {
        'name': name,
        'plan_name': plan_name,
        'amount': amount,
        'currency': currency,
        'expiry_date': expiry_date,
        'receipt_url': receipt_url,
    })

    text_content = f"""
    Hi {name},

    Your payment for {plan_name} was successful.  
    Amount: {amount} {currency}  
    Subscription valid until: {expiry_date}  

    View receipt: {receipt_url}

    Thank you for choosing ReferralPro!
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    print(f"Payment success email sent to {email}")




def send_payment_failed_email(email: str, name: str, reason: str = None):
    subject = "Your Payment Could Not Be Processed"
    from_email = settings.DEFAULT_FROM_EMAIL

    html_content = render_to_string('payment_failed.html', {
        'name': name,
        'reason': reason or "Unknown error",
        'support_url': 'https://thereferralpro.com/',
    })

    text_content = f"""
    Hi {name},

    Unfortunately, your payment could not be processed.  
    Reason: {reason or "Unknown error"}  

    Please update your card details and try again.  
    For assistance, visit: https://thereferralpro.com

    Regards,
    ReferralPro Team
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    print(f"Payment failed email sent to {email}")















