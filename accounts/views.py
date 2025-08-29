import requests
import datetime
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings
import jwt
from .models import User
from utils.email_service import send_otp, send_password_reset
from utils.otp_utils import generate_otp, verify_otp
from utils.twilio_service import TwilioService


# Utility: JWT tokens
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


# -------------------------
# Manual signup/login (Solo)
# -------------------------
class SignupView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    """Email/Password signup for Solo users only"""
    def post(self, request):
        print(request.data)
        email = request.data.get("email")
        name = request.data.get("name")
        password = request.data.get("password")
        role = request.data.get("role")

        if not email or not password:
            return Response({"error": "Email and password required"}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already registered"}, status=400)

        user = User.objects.create_user(
            email=email, password=password, full_name=name, role="solo"
        )
        tokens = get_tokens_for_user(user)

        return Response({
            "message": "Solo user registered successfully",
            "user": {"email": user.email, "name": user.full_name, "role": user.role},
            "tokens": tokens
        }, status=200)


class EmailPasswordLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    """Email/Password login (Solo users only for now)"""
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password required"}, status=400)

        user = authenticate(request, email=email, password=password)
        if not user or user.role != "solo":
            return Response({"error": "Invalid credentials or not a solo user"}, status=401)

        tokens = get_tokens_for_user(user)
        return Response({
            "user": {"email": user.email, "name": user.full_name, "role": user.role},
            "tokens": tokens
        }, status=200)


# -------------------------
# Social Logins (Solo only)
# -------------------------
class SocialLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        provider = request.data.get("provider")
        if provider not in ["google", "facebook", "apple"]:
            return Response({"error": "Invalid provider"}, status=400)

        token = request.data.get("token")
        if not token:
            return Response({"error": "Missing token"}, status=400)
        
        if user.role != "solo":
            return Response({"error": "Only solo users can use social login"}, status=403)

        try:
            if provider == "google":
                user_info = self._verify_google_token(token)
            elif provider == "facebook":
                user_info = self._verify_facebook_token(token)
            else:  # apple
                user_info = self._verify_apple_token(token)
        except Exception as e:
            return Response({"error": f"Invalid {provider} token: {str(e)}"}, status=400)

        if not user_info.get("email"):
            return Response({"error": f"{provider} did not return email"}, status=400)

        user, _ = User.objects.get_or_create(
            email=user_info["email"],
            defaults={"full_name": user_info.get("name", ""), "role": "solo"}
        )
       

        if user_info.get("picture") and not user.image:
            user.image = user_info["picture"]
            user.save()

        tokens = get_tokens_for_user(user)
        return Response({"user": {"email": user.email, "name": user.full_name, "role": user.role}, "tokens": tokens})

    def _verify_google_token(self, token):
        info = id_token.verify_oauth2_token(token, google_requests.Request())
        
        # Get user email from token info
        email = info.get("email")
        if not email:
            raise Exception("Email not found in Google token")

        
        return {
            "email": email,
            "name": info.get("name", ""),
            "picture": info.get("picture")
        }

    def _verify_facebook_token(self, token):
        fb_url = f"https://graph.facebook.com/me?fields=id,name,email,picture&access_token={token}"
        resp = requests.get(fb_url)
        if resp.status_code != 200:
            raise Exception("Invalid token")
        data = resp.json()
        return {
            "email": data.get("email"),
            "name": data.get("name"),
            "picture": data.get("picture", {}).get("data", {}).get("url")
        }

    def _verify_apple_token(self, token):
        apple_keys = requests.get("https://appleid.apple.com/auth/keys").json()["keys"]
        info = jwt.decode(
            token,
            key=apple_keys,
            algorithms=["RS256"],
            audience=settings.APPLE_BUNDLE_ID
        )
        return {
            "email": info.get("email"),
            "name": info.get("name", ""),
            "picture": None
        }


# -------------------------
# Password Reset Flow
# -------------------------
class SendOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get('email')
        phone = request.data.get('phone')

        if not email and not phone:
            return Response({"error": "Either email or phone is required"}, status=400)

        # Find user by email or phone
        try:
            if email:
                user = User.objects.get(email=email)
            else:
                user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({"error": "No account found with these credentials"}, status=404)

        # Generate OTP
        otp = generate_otp(user, purpose="password_reset", expires_in=10)

        # Send OTP via email or SMS
        try:
            if email:
                send_otp(email, otp.code)
            else:
                twilio = TwilioService()
                twilio.send_sms(phone, otp.code)
            
            return Response({"message": f"OTP sent successfully to your {'email' if email else 'phone'}"})
        except Exception as e:
            return Response({"error": f"Failed to send OTP: {str(e)}"}, status=500)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get('email')
        phone = request.data.get('phone')
        otp_code = request.data.get('otp')

        if not otp_code:
            return Response({"error": "OTP is required"}, status=400)
        if not email and not phone:
            return Response({"error": "Either email or phone is required"}, status=400)

        try:
            if email:
                user = User.objects.get(email=email)
            else:
                user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({"error": "No account found with these credentials"}, status=404)

        # Verify OTP
        is_valid, message = verify_otp(user, otp_code, purpose="password_reset")
        if not is_valid:
            return Response({"error": message}, status=400)

        # Generate a temporary token for password reset
        temp_token = RefreshToken.for_user(user)
        temp_token.set_exp(lifetime=datetime.timedelta(minutes=10))  # Token expires in 10 minutes

        return Response({
            "message": "OTP verified successfully",
            "temp_token": str(temp_token)
        })


class CreateNewPasswordView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        temp_token = request.data.get('temp_token')
        new_password = request.data.get('new_password')

        if not temp_token or not new_password:
            return Response({"error": "Temporary token and new password are required"}, status=400)

        try:
            # Decode the temporary token
            decoded_token = RefreshToken(temp_token)
            user_id = decoded_token.payload.get('user_id')
            user = User.objects.get(id=user_id)

            # Set new password
            user.set_password(new_password)
            user.save()

            # Generate new login tokens
            tokens = get_tokens_for_user(user)

            return Response({
                "message": "Password reset successful",
                "tokens": tokens
            })
        except Exception as e:
            return Response({"error": "Invalid or expired token"}, status=400)











