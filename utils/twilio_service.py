# communications/utils/twilio_service.py
from twilio.rest import Client
from django.conf import settings

class TwilioService:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def send_sms(self, phone_number: str, otp_code: str):
        message = self.client.messages.create(
            body=f"Your ReferralPro OTP code is {otp_code}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return message.sid
