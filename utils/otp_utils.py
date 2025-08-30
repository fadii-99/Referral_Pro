import random, datetime
from django.utils import timezone
from accounts.models import OtpCode

def generate_otp(user, purpose="login", expires_in=10):
    code = str(random.randint(100000, 999999))  # 6-digit OTP
    expires_at = timezone.now() + datetime.timedelta(minutes=expires_in)

    otp = OtpCode.objects.create(
        user=user,
        code=code,
        purpose=purpose,
        expires_at=expires_at
    )
    return otp

def verify_otp(user, code, purpose):
    otp = OtpCode.objects.filter(user=user, code=code, purpose=purpose, is_used=False).last()
    if not otp:
        return False, "Invalid OTP"

    if otp.expires_at < timezone.now():
        return False, "OTP expired"

    otp.is_used = True
    otp.save()
    return True, "OTP verified"
