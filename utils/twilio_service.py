from twilio.rest import Client
from django.conf import settings

class TwilioService:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def send_sms(self, phone_number: str, otp_code: str, purpose: str = "verification", expires_in: int = 10):
        message_body = (
            f"ReferralPro: Use OTP {otp_code} to {purpose.capitalize()}.\n"
            f"Expires in {expires_in} minutes.\n\n"
            "⚠️ Do not share this code with anyone."
        )

        message = self.client.messages.create(
            body=message_body,
            from_="ReferralPro",
            to=phone_number
        )
        return message.sid
