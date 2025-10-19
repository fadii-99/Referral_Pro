from twilio.rest import Client
from django.conf import settings

class TwilioService:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    @classmethod
    def send_sms(cls, phone_number: str, otp_code: str, purpose: str = "verification", expires_in: int = 10):

        service = cls()
        message_body = (
            f"ReferralPro: Use OTP {otp_code} to {purpose.capitalize()}.\n"
            f"Expires in {expires_in} minutes.\n\n"
            "⚠️ Do not share this code with anyone."
        )

        message = service.client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return message.sid

    @classmethod
    def send_app_download_sms(cls, phone_number: str, name: str, sender_name: str = None):
        print(f"Preparing to send app download SMS to {phone_number} for {name}")
        """
        Send SMS invitation to download the ReferralPro app
        """
        try:
            # Create an instance to use the client
            service = cls()
            
            message_body = (
                f"Hi {name}!\n\n"
                f"{sender_name + ' has' if sender_name else 'You have'} been invited to join ReferralPro "
                "- the app that makes referrals easy and rewarding!\n\n"
                "Create account and Register your company:\n"
                "Start building your referral network today!\n\n"
                "Best regards,\nReferralPro Team"
            )

            message = service.client.messages.create(
                body=message_body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            return {"success": True, "sid": message.sid}

        except Exception as e:
            print(f"Failed to send app download SMS to {phone_number}: {str(e)}")
            return {"success": False, "error": str(e)}


    @classmethod
    def send_referral_sms(cls, phone_number: str, referred_to_name: str, company_name: str, referred_by_name: str,reason: str = None, request_description: str = None, referral_code: str = None):
        """
        Send an SMS notification when a referral is created.
        """
        service = cls()
        
        try:
            # Format the reason and description parts
            reason_text = f"\nReason: {reason}" if reason else ""
            description_text = f"\nNotes: {request_description}" if request_description else ""
            
            message_body = (
                f"Hi {referred_to_name}!\n\n"
                f"{referred_by_name} has referred you to {company_name} via ReferralPro."
                f"{reason_text}"
                f"{description_text}\n"
                f"Referral Code: {referral_code}\n\n"
                "Regards,\nReferralPro Team"
            )

            message = service.client.messages.create(
                body=message_body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            
            print(f"Referral SMS sent to {phone_number}")
            return {"success": True, "sid": message.sid}

        except Exception as e:
            print(f"Failed to send referral SMS to {phone_number}: {str(e)}")
            return {"success": False, "error": str(e)}




