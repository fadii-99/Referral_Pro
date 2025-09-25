# django
from django.contrib.auth import authenticate
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import localtime

# rest framework
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

# models
from .models import User, FavoriteCompany, ReferralUsage, BusinessInfo
from .models import Subscription, Transaction

# utils
from utils.otp_utils import generate_otp, verify_otp
from utils.twilio_service import TwilioService
from utils.email_service import send_otp, send_invitation_email, send_company_signup_email, send_payment_failed_email, send_payment_success_email, send_solo_signup_success_email
from utils.stripe_payment import stripe_payment
from utils.storage_backends import generate_presigned_url
# google auth
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# other
import requests
import secrets
import string
import jwt
from datetime import datetime, timedelta
import json

import jwt
from jwt.algorithms import RSAAlgorithm


def generate_random_password(length=10):
    chars = string.digits + string.ascii_uppercase + string.ascii_lowercase
    return ''.join(secrets.choice(chars) for _ in range(length))



# Utility: JWT tokens
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


class checkEmailExistsView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=400)
        
        exists = User.objects.filter(email=email).exists()
        if not exists:
            return Response({"error": "Email exists, try another email"}, status=400)
        return Response({"message": "Success"}, status=200)

# -------------------------
# Manual signup/login (Solo)
# -------------------------
class SignupView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    """Email/Password signup for Solo & Business users"""
    def post(self, request):

        print("payload: ",request.data)
        

        # Handle both flat and nested payloads
        payload = request.data.get('payload')
        if payload:
            if isinstance(payload, list):  # handle QueryDict list case
                payload = payload[0]
            try:
                data = json.loads(payload)
            except Exception as e:
                print("Error parsing payload:", str(e))
                return Response({"error": f"Invalid payload format: {str(e)}"}, status=400)
        else:
            data = request.data

        # -------------------
        # BUSINESS SIGNUP
        # -------------------
        if request.data.get('role') != 'solo':

            role = data.get("welcome", {}).get("role")


            email = data.get("basic", {}).get("email") or data.get("email")
            password = data.get("password", {}).get("value")
            name = (data.get("basic", {}).get("firstName", "") + " " +
                    data.get("basic", {}).get("lastName", "")).strip() or data.get("name", "")
            
            if User.objects.filter(email=email).exists():
                return Response({"error": "Email already registered"}, status=400)

            if not email or not password:
                return Response({"error": "Email and password required"}, status=400)
            
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=name,
                phone=data.get("companyInfo", {}).get("phone", ""),
                role="company",  
                is_passwordSet=True  
            )

            # Create BusinessInfo linked to user
            business = BusinessInfo.objects.create(
                user=user,  # ✅ Add this line to link BusinessInfo to the user
                company_name=data.get("basic", {}).get("companyName", ""),
                industry=data.get("basic", {}).get("industry", ""),
                employees=data.get("businessType", {}).get("employees", ""),
                biz_type=data.get("businessType", {}).get("type", ""),
                address1=data.get("companyInfo", {}).get("address1", ""),
                address2=data.get("companyInfo", {}).get("address2", ""),
                city=data.get("companyInfo", {}).get("city", ""),
                post_code=data.get("companyInfo", {}).get("postCode", ""),
                website=data.get("companyInfo", {}).get("website", ""),
                us_state=data.get("businessType", {}).get("usState", ""),
            )
            
            user.save()

            send_company_signup_email(user.email, user.full_name)

            # Now start Stripe payment (after DB records are stored)
            try:
                # Get card details from request data
                card_info = data.get("payment", {}).get("card", {})
                card_number = card_info.get("number")
                expiry = card_info.get("expiry", {}).get("mmYY", "")
                exp_month, exp_year = (expiry.split("/") if "/" in expiry else (None, None))
                cvc = card_info.get("cvv")
                plan_name = str(data.get("subscription", {}).get("planId", "Business Plan"))
                subscription_type = data.get("subscription", {}).get("type", "monthly")  # monthly or yearly
                price = data.get("subscription", {}).get("total")  # Or get from plan/price logic
                if plan_name == '0':
                    plan_name = "Starter"
                elif plan_name == '1':
                    plan_name = "Growth"
                else:
                    plan_name = "Custom"
                # Validate card info
                if not all([card_number, exp_month, exp_year, cvc]):
                    user.delete()  # Clean up user if card details are incomplete
                    return Response({"error": "Incomplete card details"}, status=400)


                try:
                    payment_details, payment_error = stripe_payment(
                        card_number, exp_month, exp_year, cvc, price, plan_name, user.full_name
                    )

                    if not payment_details:
                        send_payment_failed_email(user.email, user.full_name, payment_error)
                        user.delete()
                        return Response({"error": f"{payment_error}"}, status=500)

                except stripe.error.CardError as e:
                    # Since it's a decline, stripe.error.CardError will be caught
                    err = e.error
                    error_msg = f"CardError: {err.message}"
                    user.delete()
                    return Response({"error": error_msg}, status=400)

                except stripe.error.RateLimitError:
                    # Too many requests
                    user.delete()
                    return Response({"error": "Too many requests made to Stripe API"}, status=429)

                except stripe.error.InvalidRequestError as e:
                    # Invalid parameters were supplied
                    user.delete()
                    return Response({"error": f"{str(e)}"}, status=400)

                except stripe.error.AuthenticationError:
                    # Invalid API key
                    user.delete()
                    return Response({"error": "Stripe authentication failed"}, status=401)

                except stripe.error.APIConnectionError:
                    # Network communication failed
                    user.delete()
                    return Response({"error": "Network error while contacting Stripe"}, status=503)

                except stripe.error.StripeError as e:
                    # Display generic error
                    user.delete()
                    return Response({"error": f"{str(e)}"}, status=500)

                except Exception as e:
                    print("Unexpected error:", str(e))
                    # Something else happened unrelated to Stripe
                    user.delete()
                    return Response({"error": f"Something Went Wrong"}, status=500)

                
               

                # Calculate subscription period end date
                if subscription_type == 'yearly':
                    period_end = timezone.now() + timedelta(days=365)
                else:  # monthly
                    period_end = timezone.now() + timedelta(days=30)

                # Create Subscription record
                subscription = Subscription.objects.create(
                    user=user,
                    plan_name=plan_name,
                    subscription_type=subscription_type,
                    price=price,
                    status='active',
                    seats_limit=data.get("subscription", {}).get("seats", 5),  # Default 5 seats for business
                    seats_used=1,  # Company owner counts as 1 seat
                    stripe_subscription_id=payment_details.get("subscription_id"),
                    stripe_customer_id=payment_details.get("customer_id"),
                    stripe_price_id=payment_details.get("price_id"),
                    stripe_product_id=payment_details.get("product_id"),
                    current_period_start=timezone.now(),
                    current_period_end=period_end
                )

                # Create Transaction record
                transaction = Transaction.objects.create(
                    user=user,
                    subscription=subscription,
                    transaction_type='subscription',
                    amount=price,
                    currency=payment_details.get("currency", "USD"),
                    status='succeeded',
                    payment_method='stripe',
                    payment_method_type=payment_details.get("payment_method_type", "card"),
                    card_brand=payment_details.get("card_brand"),
                    card_last4=payment_details.get("card_last4"),
                    card_exp_month=exp_month,
                    card_exp_year=exp_year,
                    stripe_payment_intent_id=payment_details.get("payment_intent_id"),
                    stripe_charge_id=payment_details.get("charge_id"),
                    stripe_invoice_id=payment_details.get("invoice_id"),
                    stripe_customer_id=payment_details.get("customer_id"),
                    receipt_email=user.email,
                    receipt_url=payment_details.get("receipt_url"),
                    stripe_created_at=payment_details.get("created_at")
                )

                # Mark user as paid
                user.is_paid = True
                user.save()

                send_payment_success_email(
                    user.email,
                    user.full_name,
                    plan_name,
                    price,
                    payment_details.get("currency", "USD"),
                    period_end.strftime("%Y-%m-%d"),
                    payment_details.get("receipt_url")
                )

            except Exception as e:
                print("Error during payment/subscription:", str(e))
                # Clean up user and related data if any error occurs
                user.delete()
                return Response({"error": f"{str(e)}"}, status=500)

            tokens = get_tokens_for_user(user)

            send_solo_signup_success_email(user.email, user.full_name)

            return Response({
                "message": "Business user registered and payment successful",
                "user": {
                    "email": user.email, 
                    "name": user.full_name, 
                    "role": user.role,
                },
                "tokens": tokens,
                # "payment": payment_details,
                # "subscription": {
                #     "id": subscription.id,
                #     "plan_name": subscription.plan_name,
                #     "type": subscription.subscription_type,
                #     "expires_at": subscription.current_period_end.isoformat(),
                #     "seats_limit": subscription.seats_limit,
                #     "seats_used": subscription.seats_used
                # }
            }, status=200)

        # -------------------
        # SOLO SIGNUP (unchanged)
        # -------------------
        else:
            print(request.data)

            if request.data.get("referral_code"):

                if not User.objects.filter(referral_code__iexact=request.data.get("referral_code")).exists():
                    return Response({"message": "Invalid referral code"}, status=status.HTTP_400_BAD_REQUEST)
                



            if User.objects.filter(email=request.data.get("email")).exists():
                print("Email already registered")
                return Response({"error": "Email already registered"}, status=400)

            user = User.objects.create_user(
                email=request.data.get("email"), password=request.data.get("password"), full_name=request.data.get("name"), 
                role="solo",
                phone=request.data.get("phone"),
            )
            tokens = get_tokens_for_user(user)


            if request.data.get("referral_code"):
                print("Referral code used:", request.data.get("referral_code"))
                RU = ReferralUsage.objects.create(
                    referral_code=request.data.get("referral_code"),
                    used_by=user
                )
                
            print("Solo user created:", user.email)

            return Response({
                "message": "Solo user registered successfully",
                "user": {"email": user.email, "name": user.full_name, "role": user.role},
                "tokens": tokens
            }, status=200)




class EmailPasswordLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        print(request.data)
        email = request.data.get("email")
        password = request.data.get("password")
        role = request.data.get("role")
        typee = request.data.get("type")



        if not email or not password:
            return Response({"error": "Email and password required"}, status=400)
        
        if typee == "web":
            role = "company"
        

        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                # Authentication successful, set user as active
                user.is_active = True
                user.save()
            else:
                return Response({"error": "Invalid credentials"}, status=401)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=401)
        
        if role == "rep":
            role = "employee"


        if role != user.role:
            return Response({"error": "Invalid credentials"}, status=401)
        
        tokens = get_tokens_for_user(user)
        user.is_active = True
        user.save()


        if user.role == "company":
            response = Response({
                "user": {"email": user.email, "name": user.full_name, "role": user.role, "is_paid": user.is_paid},
                "tokens": tokens
            }, status=200)
        elif user.role == "employee":
            response = Response({
                "user": {"email": user.email, "name": user.full_name, "role": user.role,  "is_passwordSet": user.is_passwordSet,},
                "tokens": tokens
            }, status=200)
        else:
            response = Response({
                "user": {"email": user.email, "name": user.full_name, "role": user.role },
                "tokens": tokens
            }, status=200)

        
        # response.set_cookie(
        #     key="access_token",
        #     value=tokens["access"],
        #     httponly=True,
        #     secure=False,
        #     samesite="None"
        # )

        return response


# -------------------------
# Social Logins (Solo only)
# -------------------------
class SocialLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        print("Social login payload:", request.data)
        provider = request.data.get("provider")
        if provider not in ["google", "facebook", "apple"]:
            return Response({"error": "Invalid provider"}, status=400)

        token = request.data.get("token")
        if not token:
            return Response({"error": "Missing token"}, status=400)
        

        try:
            if provider == "google":
                user_info = self._verify_google_token(token)
            elif provider == "facebook":
                user_info = self._verify_facebook_token(token)
            else:  # apple
                print("Verifying Apple token")
                user_info = self._verify_apple_token(token)
                if user_info.get("is_relay"):
                    return Response({"error": "hidden"}, status=400)
                print("Apple user info:", user_info)
        except Exception as e:
            return Response({"error": f"Invalid {provider} token: {str(e)}"}, status=400)

        if not user_info.get("email"):
            return Response({"error": f"{provider} did not return email"}, status=400)

        user, _ = User.objects.get_or_create(
            email=user_info["email"],
            defaults={"full_name": user_info.get("name", ""), "role": "solo"}
        )
       

        if user_info.get("name") and not user.full_name:
            user.full_name = user_info["name"]
            user.save()

        if user_info.get("picture") and not user.image:
            user.image = user_info["picture"]
            user.save()

        tokens = get_tokens_for_user(user)
        user.is_active = True
        user.save()
        return Response({"user": {"email": user.email, "name": user.full_name, "role": user.role}, "tokens": tokens})

    def _verify_google_token(self, token):
        info = id_token.verify_oauth2_token(token, google_requests.Request())

        print("\nGoogle token info:", info)
        
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

    def _verify_apple_token(self, token: str):
        # 1. Decode header to find kid
        header = jwt.get_unverified_header(token)
        kid = header["kid"]

        # 2. Fetch Apple public keys
        apple_keys = requests.get("https://appleid.apple.com/auth/keys").json()["keys"]

        # 3. Match correct key
        key = next((k for k in apple_keys if k["kid"] == kid), None)
        if not key:
            raise ValueError("Public key not found for given kid")

        # 4. Build public key
        public_key = RSAAlgorithm.from_jwk(key)

        # 5. Decode and verify JWT
        info = jwt.decode(
            token,
            key=public_key,
            algorithms=["RS256"],
            audience=settings.APPLE_BUNDLE_ID,
            issuer="https://appleid.apple.com"
        )
        print("\nApple token info:", info)
        emaill = info.get("email")
        print("\nApple email:", emaill)

        is_relay = False

        if emaill.endswith("@privaterelay.appleid.com"):
            is_relay = True


        return {
            "email": info.get("email"),
            "name": info.get("name", ""),
            "sub": info.get("sub") ,"is_relay": is_relay 
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

        print(request.data)

        if not email and not phone:
            return Response({"error": "Either email or phone is required"}, status=400)

        # Find user by email or phone
        try:
            if email:
                user = User.objects.get(email=email)
                print("user", user.email)
            else:
                user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({"error": "No account found with these credentials"}, status=404)

        # Generate OTP
        otp = generate_otp(user, purpose="password_reset", expires_in=10)
        print(otp.code)

        # Send OTP via email or SMS
        try:
            if email:
                send_otp(email, otp.code, "password reset", 10)
            else:
                # print(phone)
                twilio = TwilioService()
                twilio.send_sms(phone, otp.code, "reset password", 10)
            
            return Response({"message": f"OTP sent successfully to your {'email' if email else 'phone'}", "otp": otp.code}, status=200)
        except Exception as e:
            return Response({"error": f"Failed to send OTP: {str(e)}"}, status=500)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        print(request.data)
        email = request.data.get('email')
        otp_code = request.data.get('otp')

        phone = request.data.get('phone')
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
        temp_token.set_exp(lifetime=timedelta(minutes=10))  # Token expires in 10 minutes


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



# =========================================
# Employee Invitation & Password Setup
# =========================================
class EmployeeManagementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List employees under current company"""
        employees = User.objects.filter(parent_company=request.user, role="employee")

        employee_list = []
        for emp in employees:
            employee_list.append({
                "id": emp.id,
                "email": emp.email,
                "full_name": emp.full_name,
                "phone": emp.phone,
                "role": emp.role,
                "is_active": emp.is_active,
                "last_login": localtime(emp.last_login).strftime("%Y-%m-%d %H:%M:%S") if emp.last_login else None
            })

        return Response({"employees": employee_list}, status=status.HTTP_200_OK)

    def post(self, request):
        """Invite employee (send email + generate password)"""
        email = request.data.get("email")
        name = request.data.get("name")

        if not email or not name:
            return Response({"error": "Email and name are required"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        password = generate_random_password()

        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=name,
            role="employee",
            is_passwordSet=False,
            parent_company=request.user if request.user.role == "company" else None
        )

        try:
            send_invitation_email(email, name, password)
        except Exception as e:
            user.delete()
            return Response({"error": f"Failed to send invitation: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "message": "Invitation sent successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.full_name,
                "role": user.role
            }
        }, status=status.HTTP_200_OK)

    def put(self, request):
        """Edit employee details"""
        user_id = request.data.get("id")
        if not user_id:
            return Response({"error": "Employee ID required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id, role="employee", parent_company=request.user)
        except User.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        name = request.data.get("name")
        email = request.data.get("email")
        phone = request.data.get("phone")

        if email and User.objects.exclude(id=user_id).filter(email=email).exists():
            return Response({"error": "Email already in use"}, status=status.HTTP_400_BAD_REQUEST)

        if name:
            user.full_name = name
        if email:
            user.email = email
        if phone:
            user.phone = phone

        user.save()

        return Response({
            "message": "Employee updated successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.full_name,
                "phone": user.phone,
                "role": user.role
            }
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        """Delete employee"""
        user_id = request.GET.get("id")
        print("user_id", user_id)
        if not user_id:
            return Response({"error": "Employee ID required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id, role="employee")
        except User.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        user.delete()
        return Response({"message": "Employee deleted successfully"}, status=status.HTTP_200_OK)



class SetEmployeePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_password = request.data.get('new_password')
        print("new_password", new_password)

        if not all([ new_password]):
            return Response({"error": "new password"}, status=status.HTTP_400_BAD_REQUEST)
        

        print("request.user", request.user.id)


        try:
            user = User.objects.get(id=request.user.id)
        except User.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        
        if user.is_passwordSet:
            return Response({"error": "Password has already been set for this account."}, status=status.HTTP_400_BAD_REQUEST)

        # Set new password and update status
        user.set_password(new_password)
        user.is_passwordSet = True
        user.save()

        # Generate new login tokens for immediate login
        tokens = get_tokens_for_user(user)

        return Response({
            "message": "Password has been set successfully. You can now log in.",
            "tokens": tokens
        }, status=status.HTTP_200_OK)




class TestEmployeeManagementView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """List employees under current company"""
        employees = User.objects.filter(parent_company=request.user, role="employee")

        employee_list = []
        for emp in employees:
            employee_list.append({
                "id": emp.id,
                "email": emp.email,
                "full_name": emp.full_name,
                "phone": emp.phone,
                "role": emp.role,
                "is_active": emp.is_active,
                "last_login": localtime(emp.last_login).strftime("%Y-%m-%d %H:%M:%S") if emp.last_login else None
            })

        return Response({"employees": employee_list}, status=status.HTTP_200_OK)





class SendResetPasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        print(request.GET.get("id"))
        id = request.GET.get("id")
        if not id:
            return Response({"error": "data is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        new_password = generate_random_password()
        user.set_password(new_password)
        user.is_passwordSet = False
        user.save()

        try:
            send_invitation_email(user.email, user.full_name, new_password)
        except Exception as e:
            return Response({"error": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Password reset and emailed successfully"}, status=status.HTTP_200_OK)




# ==========================================
# ==========================================



class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = User.objects.get(id=request.user.id)
        # image_url = user.get_image_url()
        image_url = None
        if user.image and hasattr(user.image, 'url'):
            try:
                # Check if it's a URL (from social login) or a file
                if str(user.image).startswith(('http://', 'https://')):
                    # It's a URL from social login
                    image_url = str(user.image)
                else:
                    # It's a file stored in storage
                    print("user.image", user.image)
                    image_url = generate_presigned_url(f"media/{user.image}", expires_in=3600)
                    # image_url = f"{settings.MEDIA_URL}{user.image}" if user.image else None
            except (ValueError, FileNotFoundError):
                # Handle cases where file doesn't exist or invalid URL
                image_url = None
        print("image_url", image_url)
        return Response({
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "role": user.role,
                "image": image_url,
                "is_passwordSet": user.is_passwordSet,
                "is_paid": user.is_paid
            },
        }, status=200)


class UpdateUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data
        print("UpdateUserView data", request.FILES)
        
        # Handle image upload separately since it's a file
        if 'image' in request.FILES:
            user.image = request.FILES['image']
        
        # Fields that can be updated for User model (excluding image since we handle it above)
        updatable_user_fields = ['full_name', 'phone']
        
        # Update user fields
        for field in updatable_user_fields:
            if field in data:
                setattr(user, field, data[field])
        
        try:
            user.save()
            
            # Update business info if user has business_info and data is provided
            business_data = data.get('business_info', {})
            if hasattr(user, 'business_info') and business_data:
                business_info = user.business_info
                
                # Fields that can be updated for BusinessInfo model
                updatable_business_fields = [
                    'company_name', 'industry', 'employees', 'biz_type',
                    'address1', 'address2', 'city', 'post_code', 'website', 'us_state'
                ]
                
                for field in updatable_business_fields:
                    if field in business_data:
                        setattr(business_info, field, business_data[field])
                
                business_info.save()
            
            # Prepare response data
            response_data = {
                "message": "User updated successfully",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "phone": user.phone,
                    "image": user.image.url if user.image else None,
                    "role": user.role,
                    "is_verified": user.is_verified,
                }
            }
            
            # Include business info in response if it exists
            if hasattr(user, 'business_info'):
                business_info = user.business_info
                response_data["business_info"] = {
                    "company_name": business_info.company_name,
                    "industry": business_info.industry,
                    "employees": business_info.employees,
                    "biz_type": business_info.biz_type,
                    "address1": business_info.address1,
                    "address2": business_info.address2,
                    "city": business_info.city,
                    "post_code": business_info.post_code,
                    "website": business_info.website,
                    "us_state": business_info.us_state,
                }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(str(e))
            return Response(
                {"error": f"Failed to update user: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


    def get(self, request):
        """Get current user profile"""
        user = request.user
        
        response_data = {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "image": user.image.url if user.image else None,
                "role": user.role,
                "is_verified": user.is_verified,
                "is_paid": user.is_paid,
            }
        }
        
        # Include business info if it exists
        if hasattr(user, 'business_info'):
            business_info = user.business_info
            response_data["business_info"] = {
                "company_name": business_info.company_name,
                "industry": business_info.industry,
                "employees": business_info.employees,
                "biz_type": business_info.biz_type,
                "address1": business_info.address1,
                "address2": business_info.address2,
                "city": business_info.city,
                "post_code": business_info.post_code,
                "website": business_info.website,
                "us_state": business_info.us_state,
            }
        
        return Response(response_data, status=status.HTTP_200_OK)  




# -------------------------
# Delete User by Email
# -------------------------
class DeleteUsersByIdsView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        ids_to_delete = [42]

        # Get all users that match the IDs
        users = User.objects.filter(id__in=ids_to_delete)
        found_ids = list(users.values_list("id", flat=True))

        if not users.exists():
            return Response({"error": "No users found with the given IDs."}, status=404)

        # Delete all matched users
        # users.delete()

        return Response({
            "message": f"Users with IDs {found_ids} deleted successfully.",
            "count_deleted": len(found_ids)
        }, status=200)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # refresh_token = request.data.get('refresh')
        # if not refresh_token:
        #     return Response({"error": "Refresh token required."}, status=400)
        try:
            # token = RefreshToken(refresh_token)
            # token.blacklist()
            # Deactivate user
            user = request.user
            user.is_active = False
            user.save()
            return Response({"message": "Logout successful."}, status=200)
        except TokenError:
            return Response({"error": "Invalid or expired token."}, status=400)





class AccountDeletionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Verify OTP and delete account"""
        temp_token = request.data.get('temp_token')


        if not temp_token:
            return Response({"error": "OTP is required"}, status=400)
        
        # decoded_token = RefreshToken(temp_token)
        # user_id = decoded_token.payload.get('user_id')
        # user = User.objects.get(id=user_id)

        user = request.user


        user_email = user.email
        user_name = user.full_name
        user_role = user.role

        try:
            # If user is a company, handle employee cleanup
            if user.role == "company":
                # Delete all employees under this company
                employees = User.objects.filter(parent_company=user, role="employee")
                employee_count = employees.count()
                employees.delete()
                
                # Delete business info if exists
                if hasattr(user, 'business_info'):
                    user.business_info.delete()
                
                # Cancel subscriptions if any
                if hasattr(user, 'subscriptions'):
                    # Note: You might want to add Stripe subscription cancellation logic here
                    user.subscriptions.all().delete()
                
                # Delete transactions
                if hasattr(user, 'transactions'):
                    user.transactions.all().delete()

            # Delete favorite companies
            FavoriteCompany.objects.filter(user=user).delete()
            
            # Delete referral usage records
            ReferralUsage.objects.filter(used_by=user).delete()
            
            # Finally delete the user
            # user.delete()
            user.is_delete = True
            user.is_active = False
            user.email = user.email + f"_deleted"
            user.phone = user.phone + f"_deleted" if user.phone else None
            user.save()


            response_message = f"Account deleted successfully for {user_email}"
            if user_role == "company" and 'employee_count' in locals():
                response_message += f" along with {employee_count} employee accounts"

            return Response({
                "message": response_message,
                "deleted_user": {
                    "email": user_email,
                    "name": user_name,
                    "role": user_role
                }
            }, status=200)

        except Exception as e:
            return Response({
                "error": f"Failed to delete account: {str(e)}"
            }, status=500)


class ResetPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(request.data)
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response({"error": "Both current password and new password are required"}, status=400)

        user = request.user

        # Verify current password
        if not user.check_password(current_password):
            return Response({"error": "Current password is incorrect"}, status=400)

        # Check if new password is different from current
        if user.check_password(new_password):
            return Response({"error": "New password must be different from current password"}, status=400)

        # Set new password
        user.set_password(new_password)
        user.save()

        return Response({
            "message": "Password reset successfully"
        }, status=200)









