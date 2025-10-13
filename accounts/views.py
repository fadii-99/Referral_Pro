# django
from django.contrib.auth import authenticate
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import localtime
from django.db import models

# rest framework
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

# models
from .models import User, FavoriteCompany, ReferralUsage, BusinessInfo, Device, Review, ReviewImage
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
            return Response({"message": "Success"}, status=200)
        return Response({"error": "Email exists, try another email"}, status=400)
        

class checkPhoneExistsView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        phone = request.data.get("phone")
        print(phone)
        if not phone:
            return Response({"error": "Phone is required"}, status=400)

        exists = User.objects.filter(phone=phone).exists()
        if not exists:
            return Response({"message": "Success"}, status=200)
        return Response({"error": "Phone exists, try another phone"}, status=400)
        

# -------------------------
# Manual signup/login (Solo)
# -------------------------
class SignupView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    """Email/Password signup for Solo & Business users"""
    def post(self, request):

        

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
            
            if User.objects.filter(phone=data.get("companyInfo", {}).get("phone", "")).exists():
                return Response({"error": "Phone number already registered"}, status=400)
            
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
                        # Send internal email with full error for your team
                        send_payment_failed_email(user.email, user.full_name, payment_error)

                        # Delete user if needed
                        user.delete()

                        # Show polished message to end-user
                        return Response(
                            {"error": "Your payment could not be processed. Please check your card details or try another payment method."},
                            status=400
                        )

                except Exception as e:
                    print("Stripe payment exception:", str(e))
                    user.delete()

                    # Show only clean message to customer
                    return Response(
                        {"error": err.message or "Your card was declined. Please try a different card."},
                        status=400
                    )

                # except stripe.error.RateLimitError:
                #     # Too many requests
                #     user.delete()
                #     return Response({"error": "Too many requests made to Stripe API"}, status=429)

                # except stripe.error.InvalidRequestError as e:
                #     # Invalid parameters were supplied
                #     user.delete()
                #     return Response({"error": f"{str(e)}"}, status=400)

                # except stripe.error.AuthenticationError:
                #     # Invalid API key
                #     user.delete()
                #     return Response({"error": "Stripe authentication failed"}, status=401)

                # except stripe.error.APIConnectionError:
                #     # Network communication failed
                #     user.delete()
                #     return Response({"error": "Network error while contacting Stripe"}, status=503)

                # except stripe.error.StripeError as e:
                #     # Display generic error
                #     user.delete()
                #     return Response({"error": f"{str(e)}"}, status=500)

                # except Exception as e:
                #     print("Unexpected error:", str(e))
                #     # Something else happened unrelated to Stripe
                #     user.delete()
                #     return Response({"error": f"Something Went Wrong"}, status=500)

                
               

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
        # else:
        #     print(request.data)

        #     if request.data.get("referral_code"):

        #         if not User.objects.filter(referral_code__iexact=request.data.get("referral_code")).exists():
        #             return Response({"message": "Invalid referral code"}, status=status.HTTP_400_BAD_REQUEST)
                



        #     if User.objects.filter(email=request.data.get("email")).exists():
        #         print("Email already registered")
        #         return Response({"error": "Email already registered"}, status=400)


        #     if request.data.get("phone"):
        #         if User.objects.filter(phone=request.data.get("phone")).exists():
        #             return Response({"error": "Phone number already registered"}, status=400)
            

        #     user = User.objects.create_user(
        #         email=request.data.get("email"), password=request.data.get("password"), full_name=request.data.get("name"), 
        #         role="solo",
        #         phone=request.data.get("phone"),
        #     )
        #     tokens = get_tokens_for_user(user)


        #     if request.data.get("referral_code"):
        #         print("Referral code used:", request.data.get("referral_code"))
        #         RU = ReferralUsage.objects.create(
        #             referral_code=request.data.get("referral_code"),
        #             used_by=user
        #         )
                
        #     print("Solo user created:", user.email)

        #     return Response({
        #         "message": "Solo user registered successfully",
        #         "user": {"email": user.email, "name": user.full_name, "role": user.role},
        #         "tokens": tokens
        #     }, status=200)


        else:
            try:
                phone = request.data.get("phone")
                user = None

                if request.data.get("referral_code"):

                    if not User.objects.filter(referral_code__iexact=request.data.get("referral_code")).exists():
                        return Response({"message": "Invalid referral code"}, status=status.HTTP_400_BAD_REQUEST)
                existing_user = None
                try:
                    existing_user = User.objects.get(email=request.data.get("email"))
                except User.DoesNotExist:
                    print("No existing user with this email")


                if existing_user:
                    if existing_user.is_to_be_registered:
                        try:
                            existing_user.full_name = request.data.get("name")


                            existing_user.set_password(request.data.get("password"))
                            existing_user.is_to_be_registered = False
                            existing_user.phone = phone
                            existing_user.save()

                            tokens = get_tokens_for_user(existing_user)


                            if request.data.get("referral_code"):
                                RU = ReferralUsage.objects.create(
                                    referral_code=request.data.get("referral_code"),
                                    used_by=existing_user
                                )
                                

                            return Response({
                                "message": "Solo user registered successfully",
                                "user": {"email": existing_user.email, "name": existing_user.full_name, "role": existing_user.role},
                                "tokens": tokens
                            }, status=200)
                        except Exception as e:
                            print("Error registering to-be-registered user:", str(e))
                            return Response({"error": "Failed to complete registration. Please try again."}, status=500)
                else:
                    print("Creating new solo user")
                    if User.objects.filter(email=request.data.get("email")).exists():
                        return Response({"error": "Email already registered"}, status=400)


                    if request.data.get("phone"):
                        if User.objects.filter(phone=request.data.get("phone")).exists():
                            return Response({"error": "Phone number already registered"}, status=400)
                    

                    user = User.objects.create_user(
                        email=request.data.get("email"), password=request.data.get("password"), full_name=request.data.get("name"), 
                        role="solo",
                        phone=request.data.get("phone"),
                    )

                    tokens = get_tokens_for_user(user)


                    if request.data.get("referral_code"):
                        RU = ReferralUsage.objects.create(
                            referral_code=request.data.get("referral_code"),
                            used_by=user
                        )

                    send_solo_signup_success_email(user.email, user.full_name)
                        

                    return Response({
                        "message": "Solo user registered successfully",
                        "user": {"email": user.email, "name": user.full_name, "role": user.role},
                        "tokens": tokens
                    }, status=200)
            except Exception as e:
                print("Error during solo signup:", str(e))

                if str(e) == 'list index out of range':
                    return Response({"error": "Invalid payload format"}, status=400)

                return Response({"error": "Failed to register user. Please try again."}, status=500)
class EmailPasswordLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
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


        if user.role == "admin":
            response = Response({
                "user": {"email": user.email, "name": user.full_name, "role": user.role},
                "tokens": tokens
            }, status=200)
        elif user.role == "company":
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
                user_info = self._verify_apple_token(token)
                if user_info.get("is_relay"):
                    return Response({"error": "hidden"}, status=400)
        except Exception as e:
            return Response({"error": f"Invalid {provider} token: {str(e)}"}, status=400)

        if not user_info.get("email"):
            return Response({"error": f"{provider} did not return email"}, status=400)

        # Check if user already exists
        try:
            existing_user = User.objects.get(email=user_info["email"])
            
            # Handle to-be-registered users
            if existing_user.is_to_be_registered:
                try:
                    # Complete registration for existing to-be-registered user
                    if user_info.get("name") and not existing_user.full_name:
                        existing_user.full_name = user_info["name"]
                    
                    existing_user.is_to_be_registered = False
                    existing_user.social_platform = user_info["platform"]
                    
                    if user_info.get("picture") and not existing_user.image:
                        existing_user.image = user_info["picture"]
                    
                    existing_user.save()

                    tokens = get_tokens_for_user(existing_user)
                    existing_user.is_active = True
                    existing_user.save()

                    return Response({
                        "message": "Social login registration completed successfully",
                        "user": {"email": existing_user.email, "name": existing_user.full_name, "role": existing_user.role},
                        "tokens": tokens
                    }, status=200)
                    
                except Exception as e:
                    print("Error completing social registration for to-be-registered user:", str(e))
                    return Response({"error": "Failed to complete social registration. Please try again."}, status=500)
            
            else:
                # Existing user - normal login flow
                if existing_user.role != "solo":
                    return Response({"error": "This email already exists as " + existing_user.role}, status=400)

                # Update user info if missing
                if user_info.get("name") and not existing_user.full_name:
                    existing_user.full_name = user_info["name"]
                    existing_user.save()

                if user_info.get("picture") and not existing_user.image:
                    existing_user.image = user_info["picture"]
                    existing_user.save()

                tokens = get_tokens_for_user(existing_user)
                existing_user.is_active = True
                existing_user.save()
                
                return Response({
                    "user": {"email": existing_user.email, "name": existing_user.full_name, "role": existing_user.role}, 
                    "tokens": tokens
                })

        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_user(
                email=user_info["email"],
                social_platform=user_info["platform"],
                full_name=user_info.get("name", ""),
                role="solo",
                image=user_info.get("picture")
            )

            tokens = get_tokens_for_user(user)
            user.is_active = True
            user.save()
            
            return Response({
                "user": {"email": user.email, "name": user.full_name, "role": user.role}, 
                "tokens": tokens
            })




# -------------------------
# Password Reset Flow
# -------------------------
class SendOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get('email')
        phone = request.data.get('phone')



        # Find user by email or phone
        try:
            if email:
                user = User.objects.get(email=email)
            else:
                user = User.objects.get(phone=phone)
        except User.DoesNotExist as e:
            print("No user found with given email/phone", str(e))
            return Response({"error": "No account found with these credentials"}, status=404)

        if user.role != request.data.get('role'):
            return Response({"error": f"Unauthorized access: your profile type does not match this endpoint."}, status=404)

        # Generate OTP
        otp = generate_otp(user, purpose="password_reset", expires_in=10)

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
            print("Error sending OTP:", str(e))
            return Response({"error": f"Failed to send OTP: {str(e)}"}, status=500)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
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

        if not all([ new_password]):
            return Response({"error": "new password"}, status=status.HTTP_400_BAD_REQUEST)
        

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

import json
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from datetime import datetime

class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = User.objects.get(id=request.user.id)
        image_url = None

        if user.image and hasattr(user.image, 'url'):
            try:
                if str(user.image).startswith(('http://', 'https://')):
                    image_url = str(user.image)
                else:
                    image_url = generate_presigned_url(f"media/{user.image}", expires_in=3600)
            except (ValueError, FileNotFoundError):
                image_url = None



        # Base user response
        response_data = {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "role": user.role,
                "image": image_url,
                "is_passwordSet": user.is_passwordSet,
                "is_paid": user.is_paid,

            }
        }

        # Add business info if exists
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
            response_data["user"]["company_name"] =  business_info.company_name


        

        return Response(response_data, status=200)



class UpdateUserView(APIView):
    permission_classes = [IsAuthenticated]


    def post(self, request):
        
        user = request.user
        data = request.data



        # Parse business_info properly
        business_data = data.get("business_info", {})
        if isinstance(business_data, str):
            try:
                business_data = json.loads(business_data)
            except json.JSONDecodeError:
                return Response(
                    {"error": "Invalid business_info format"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Handle image upload separately
        if "image" in request.FILES:
            user.image = request.FILES["image"]

        if data.get("phone"):
            if User.objects.exclude(id=user.id).filter(phone=data.get("phone")).exists():
                return Response({"error": "Phone number already registered"}, status=400)

        # Updatable fields
        updatable_user_fields = ["full_name", "phone"]

        for field in updatable_user_fields:
            if field in data:
                setattr(user, field, data[field])

        try:
            user.save()

            # Update Business Info if exists
            if hasattr(user, "business_info") and business_data:
                business_info = user.business_info
                updatable_business_fields = [
                    "company_name", "industry", "employees", "biz_type",
                    "address1", "address2", "city", "post_code", "website", "us_state"
                ]
                for field in updatable_business_fields:
                    if field in business_data:
                        setattr(business_info, field, business_data[field])
                business_info.save()

            return Response({"message": "User updated successfully"}, status=200)

        except Exception as e:
            return Response(
                {"error": f"Failed to update user: {str(e)}"},
                status=500
            )


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

    def delete(self, request):
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

            Device.objects.filter(user=user).delete()

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



from firebase_admin import messaging

class RegisterFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            token = request.data.get("token")
            platform = request.data.get("platform", "Android")

            if not token:
                return Response({"error": "Token is required"}, status=400)

            # Optional: Validate token with Firebase
            try:
                # This will throw an exception if token is invalid
                messaging.Message(token=token)
            except Exception:
                return Response({"error": "Invalid FCM token"}, status=400)

            # Remove any existing instances of this token
            Device.objects.filter(token=token).delete()
            
            # Create new device record for current user
            Device.objects.create(
                user=request.user,
                token=token,
                platform=platform
            )
            
            return Response({"message": "Token registered successfully"})
            
        except Exception as e:
            print("Error registering FCM token:", str(e))
            return Response({"error": "Failed to register token"}, status=500)




class UnregisterFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        token = request.data.get("token")
        if token:
            Device.objects.filter(user=request.user, token=token).delete()
        return Response({"message": "Token removed"})


# ==========================================
# REVIEW MANAGEMENT APIS
# ==========================================
class ReviewManagementView(APIView):
    """
    Handle review operations: Create, List, Update, Delete
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create a new review (Solo users only)"""
        print(request.data)
        
        # if request.user.role != 'solo':
        #     return Response({"error": "Only solo users can create reviews"}, status=403)
        
        # Extract data from request
        business_id = request.data.get('business_id')
        review_rating = request.data.get('review_rating')
        review_feedback = request.data.get('review_feedback', '')
        
        # Validation
        if not business_id:
            return Response({"error": "Business ID is required"}, status=400)
        
        if not review_rating:
            return Response({"error": "Review rating is required"}, status=400)
        
        try:
            review_rating = int(review_rating)
            if review_rating < 1 or review_rating > 5:
                return Response({"error": "Review rating must be between 1 and 5"}, status=400)
        except (ValueError, TypeError):
            return Response({"error": "Review rating must be a valid number"}, status=400)
        
        # Check if business exists
        try:
            business = User.objects.get(id=business_id, role='company')
        except User.DoesNotExist:
            return Response({"error": "Business not found"}, status=404)
        
        # Check if user already reviewed this business
        existing_review = Review.objects.filter(review_by=request.user, business=business).first()
        if existing_review:
            return Response({"error": "You have already reviewed this business"}, status=400)
        
        try:
            # Create the review
            review = Review.objects.create(
                business=business,
                review_by=request.user,
                review_rating=review_rating,
                review_feedback=review_feedback
            )
            
            # Handle image uploads if any
            images = request.FILES.getlist('images')
            review_images = []
            
            for image in images:
                review_image = ReviewImage.objects.create(
                    review=review,
                    image=image
                )
                review_images.append({
                    "id": review_image.id,
                    "image_url": generate_presigned_url(f"media/{review_image.image}", expires_in=3600) if review_image.image else None
                })
            
            # Prepare response data
            business_name = business.business_info.company_name if hasattr(business, 'business_info') else business.full_name or business.email
            reviewer_image_url = None
            
            if request.user.image:
                try:
                    if str(request.user.image).startswith(('http://', 'https://')):
                        reviewer_image_url = str(request.user.image)
                    else:
                        reviewer_image_url = generate_presigned_url(f"media/{request.user.image}", expires_in=3600)
                except (ValueError, FileNotFoundError):
                    reviewer_image_url = None
            
            review_data = {
                "id": review.id,
                "business": {
                    "id": business.id,
                    "name": business_name,
                    "email": business.email
                },
                "review_by": {
                    "id": request.user.id,
                    "name": request.user.full_name or request.user.email,
                    "image": reviewer_image_url
                },
                "review_rating": review.review_rating,
                "review_feedback": review.review_feedback,
                "images": review_images,
                "created_at": review.created_at.isoformat(),
                "updated_at": review.updated_at.isoformat() if review.updated_at else None
            }
            
            return Response({
                "message": "Review created successfully",
                "review": review_data
            }, status=201)
            
        except Exception as e:
            print(str(e))
            return Response({"error": f"Failed to create review: {str(e)}"}, status=500)
    
    def get(self, request):
        """List reviews - different behavior based on user role"""
        from .serializers import ReviewSerializer, BusinessReviewListSerializer
        
        business_id = request.GET.get('business_id')
        print("Business ID:", business_id)
        
        if request.user.role == 'solo':
            if business_id:
                try:
                    business = User.objects.get(id=business_id, role='company')
                except User.DoesNotExist:
                    return Response({"error": "Business not found"}, status=404)

                reviews = Review.objects.filter(business=business).select_related("review_by")
                total_reviews = reviews.count()

                # Check if current user has reviewed this business
                user_review = reviews.filter(review_by=request.user).first()

                print("User Review:", user_review.user.full_name)

                # Pagination params
                page = int(request.GET.get('page', 1))
                limit = int(request.GET.get('limit', 10))
                offset = (page - 1) * limit

                # --- Ensure user's review appears first ---
                if user_review:
                    # All other reviews excluding current user's
                    other_reviews = reviews.exclude(id=user_review.id).order_by('-updated_at')

                    if offset == 0:
                        # First page: show user's review first
                        remaining = limit - 1  # one slot reserved for user review
                        other_page = list(other_reviews[:remaining])
                        paginated_reviews = [user_review] + other_page
                    else:
                        # For next pages, offset shifts since user_review was already shown
                        adj_offset = offset - 1
                        paginated_reviews = list(other_reviews[adj_offset:adj_offset + limit])
                else:
                    # If user has not reviewed yet — normal pagination
                    paginated_reviews = list(reviews.order_by('-updated_at')[offset:offset + limit])

                # --- Serialize with flags ---
                serialized_reviews = []
                for review in paginated_reviews:
                    data = BusinessReviewListSerializer(review).data
                    data["is_my_review"] = review.review_by_id == request.user.id
                    data["can_edit"] = review.review_by_id == request.user.id
                    serialized_reviews.append(data)

                # --- Rating statistics ---
                stats = reviews.aggregate(
                    avg_rating=models.Avg('review_rating'),
                    total_reviews=models.Count('id'),
                    five_star=models.Count('id', filter=models.Q(review_rating=5)),
                    four_star=models.Count('id', filter=models.Q(review_rating=4)),
                    three_star=models.Count('id', filter=models.Q(review_rating=3)),
                    two_star=models.Count('id', filter=models.Q(review_rating=2)),
                    one_star=models.Count('id', filter=models.Q(review_rating=1)),
                )

                business_info = {
                    "id": business.id,
                    "name": getattr(business.business_info, "company_name", business.full_name or business.email),
                    "email": business.email
                }

                return Response({
                    "business": business_info,
                    "reviews": serialized_reviews,
                    "user_review_status": {
                        "has_reviewed": user_review is not None,
                        "user_review_id": user_review.id if user_review else None,
                        "can_review": user_review is None,
                        "can_edit": user_review is not None
                    },
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": total_reviews,
                        "has_next": offset + limit < total_reviews,
                        "has_previous": page > 1
                    },
                    "statistics": {
                        "average_rating": round(stats['avg_rating'], 2) if stats['avg_rating'] else 0,
                        "total_reviews": stats['total_reviews'],
                        "rating_breakdown": {
                            "5_star": stats['five_star'],
                            "4_star": stats['four_star'],
                            "3_star": stats['three_star'],
                            "2_star": stats['two_star'],
                            "1_star": stats['one_star'],
                        }
                    }
                })
            else:
                # Solo users see their own reviews (existing functionality)
                reviews = Review.objects.filter(review_by=request.user)
                serializer = ReviewSerializer(reviews, many=True, context={'request': request})
                
                return Response({
                    "message": "Your reviews retrieved successfully",
                    "reviews": serializer.data,
                    "count": reviews.count()
                })
            
        elif request.user.role == 'company':
            # Companies see reviews about their business
            reviews = Review.objects.filter(business=request.user)
            serializer = BusinessReviewListSerializer(reviews, many=True)
            
            # Calculate average rating
            avg_rating = reviews.aggregate(
                avg_rating=models.Avg('review_rating')
            )['avg_rating']
            
            return Response({
                "message": "Reviews for your business retrieved successfully",
                "reviews": serializer.data,
                "count": reviews.count(),
                "average_rating": round(avg_rating, 2) if avg_rating else 0
            })
        
        else:
            return Response({"error": "Unauthorized access"}, status=403)
    
    def put(self, request):
        """Update an existing review (Only review author can edit)"""
        
        review_id = request.data.get('review_id')
        if not review_id:
            return Response({"error": "Review ID is required"}, status=400)
        
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)
        
        # Check if the current user is the author of the review
        if review.review_by != request.user:
            return Response({"error": "You can only edit your own reviews"}, status=403)
        
        # Check if user is trying to change the business (not allowed)
        if 'business' in request.data or 'business_id' in request.data:
            return Response({"error": "Cannot change the business for an existing review"}, status=400)
        
        try:
            # Update review rating if provided
            if 'review_rating' in request.data:
                rating = request.data.get('review_rating')
                try:
                    rating = int(rating)
                    if rating < 1 or rating > 5:
                        return Response({"error": "Review rating must be between 1 and 5"}, status=400)
                    review.review_rating = rating
                except (ValueError, TypeError):
                    return Response({"error": "Review rating must be a valid number"}, status=400)
            
            # Update review feedback if provided
            if 'review_feedback' in request.data:
                review.review_feedback = request.data.get('review_feedback', '')
            
            # Save the review updates
            review.save()
            
            # Handle image updates if provided
            new_images = request.FILES.getlist('images')
            if new_images:
                # Optional: Remove existing images if replace_images flag is set
                if request.data.get('replace_images', False):
                    ReviewImage.objects.filter(review=review).delete()
                
                # Add new images
                for image in new_images:
                    ReviewImage.objects.create(
                        review=review,
                        image=image
                    )
            
            # Handle removing specific images by ID
            remove_image_ids = request.data.get('remove_image_ids', [])
            if remove_image_ids:
                if isinstance(remove_image_ids, str):
                    try:
                        remove_image_ids = [int(id.strip()) for id in remove_image_ids.split(',')]
                    except ValueError:
                        return Response({"error": "Invalid image IDs format"}, status=400)
                
                ReviewImage.objects.filter(
                    review=review, 
                    id__in=remove_image_ids
                ).delete()
            
            # Prepare response data
            reviewer_image_url = None
            if review.review_by.image:
                try:
                    if str(review.review_by.image).startswith(('http://', 'https://')):
                        reviewer_image_url = str(review.review_by.image)
                    else:
                        reviewer_image_url = generate_presigned_url(f"media/{review.review_by.image}", expires_in=3600)
                except (ValueError, FileNotFoundError):
                    reviewer_image_url = None
            
            # Get updated review images
            review_images = []
            for img in ReviewImage.objects.filter(review=review):
                try:
                    if str(img.image).startswith(('http://', 'https://')):
                        image_url = str(img.image)
                    else:
                        image_url = generate_presigned_url(f"media/{img.image}", expires_in=3600)
                    
                    review_images.append({
                        "id": img.id,
                        "image_url": image_url,
                        "uploaded_at": img.uploaded_at.isoformat() if img.uploaded_at else None
                    })
                except (ValueError, FileNotFoundError):
                    continue
            
            business_name = review.business.business_info.company_name if hasattr(review.business, 'business_info') else review.business.full_name or review.business.email
            
            review_data = {
                "id": review.id,
                "business": {
                    "id": review.business.id,
                    "name": business_name,
                    "email": review.business.email
                },
                "review_by": {
                    "id": review.review_by.id,
                    "name": review.review_by.full_name or review.review_by.email,
                    "image": reviewer_image_url
                },
                "review_rating": review.review_rating,
                "review_feedback": review.review_feedback,
                "images": review_images,
                "time_ago": review.time_ago(),
                "created_at": review.created_at.isoformat(),
                "updated_at": review.updated_at.isoformat() if review.updated_at else None,
                "is_current_user_review": True  # Always true since only owner can edit
            }
            
            return Response({
                "message": "Review updated successfully",
                "review": review_data
            }, status=200)
            
        except Exception as e:
            return Response({"error": f"Failed to update review: {str(e)}"}, status=500)
    
    def delete(self, request):
        """Delete a review (Only review author can delete)"""
        review_id = request.data.get('review_id') or request.GET.get('review_id')
        if not review_id:
            return Response({"error": "Review ID is required"}, status=400)
        
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)
        
        # Check if the current user is the author of the review
        if review.review_by != request.user:
            return Response({"error": "You can only delete your own reviews"}, status=403)
        
        business_name = review.business.business_info.company_name if hasattr(review.business, 'business_info') else review.business.full_name
        review.delete()
        
        return Response({
            "message": f"Review for {business_name} deleted successfully"
        }, status=200)



class BusinessReviewsView(APIView):
    """
    Public endpoint to get reviews for a specific business
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, business_id):
        try:
            from django.db import models
            from django.utils import timezone
            from utils.storage_backends import generate_presigned_url

            # ---- Fetch business ----
            try:
                business = User.objects.get(id=business_id, role="company")
            except User.DoesNotExist:
                return Response({"error": "Business not found"}, status=404)

            # ---- Fetch all reviews for this business ----
            reviews = Review.objects.filter(business=business).select_related("review_by")

            # ---- Pagination setup ----
            page = int(request.GET.get("page", 1))
            limit = int(request.GET.get("limit", 10))
            offset = (page - 1) * limit
            total_reviews = reviews.count()

            # ---- Ensure current user review is first ----
            user_review = reviews.filter(review_by_id=request.user.id).first()
            if user_review:
                other_reviews = reviews.exclude(id=user_review.id).order_by("-created_at")
                if offset == 0:
                    remaining_slots = limit - 1  # first slot reserved for user's review
                    paginated_reviews = [user_review] + list(other_reviews[:remaining_slots])
                else:
                    adjusted_offset = offset - 1  # shift pagination since first page had 1 extra
                    paginated_reviews = list(other_reviews[adjusted_offset:adjusted_offset + limit])
            else:
                paginated_reviews = list(reviews.order_by("-created_at")[offset:offset + limit])

            # ---- Statistics ----
            stats = reviews.aggregate(
                avg_rating=models.Avg("review_rating"),
                total_reviews=models.Count("id"),
                five_star=models.Count("id", filter=models.Q(review_rating=5)),
                four_star=models.Count("id", filter=models.Q(review_rating=4)),
                three_star=models.Count("id", filter=models.Q(review_rating=3)),
                two_star=models.Count("id", filter=models.Q(review_rating=2)),
                one_star=models.Count("id", filter=models.Q(review_rating=1)),
            )

            # ---- Helper: presign images ----
            def _presigned_or_public(path):
                if not path:
                    return None
                s = str(path)
                if s.startswith(("http://", "https://")):
                    return s
                try:
                    return generate_presigned_url(f"media/{s}", expires_in=3600)
                except Exception:
                    return None

            # ---- Build review data ----
            reviews_data = []
            for review in paginated_reviews:
                # Time ago using helper from model
                time_ago = review.time_ago()

                # Reviewer image
                reviewer_image_url = _presigned_or_public(getattr(review.review_by, "image", None))

                # Review images
                review_gallery = []
                try:
                    for img in ReviewImage.objects.filter(review=review)[:3]:
                        image_url = _presigned_or_public(img.image)
                        if image_url:
                            review_gallery.append({
                                "id": img.id,
                                "image_url": image_url,
                                "uploaded_at": img.uploaded_at.isoformat() if img.uploaded_at else None,
                            })
                except Exception as e:
                    print(f"Error fetching review images: {str(e)}")

                reviews_data.append({
                    "id": review.id,
                    "review_rating": review.review_rating,
                    "time_ago": time_ago,
                    "review_feedback": review.review_feedback,
                    "review_by": review.review_by.full_name or review.review_by.email,
                    "review_by_image": reviewer_image_url,
                    "review_gallery": review_gallery,
                    "user_id": review.review_by.id,
                    "created_at": review.created_at.isoformat(),
                    "updated_at": review.updated_at.isoformat() if review.updated_at else None,
                    "is_current_user_review": review.review_by_id == request.user.id,
                })

            # ---- Business info ----
            business_info = {
                "id": business.id,
                "name": getattr(business.business_info, "company_name", business.full_name or business.email),
                "email": business.email,
            }

            # ---- Response ----
            return Response({
                "business": business_info,
                "reviews": reviews_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_reviews,
                    "has_next": offset + limit < total_reviews,
                    "has_previous": page > 1,
                },
                "statistics": {
                    "average_rating": round(stats["avg_rating"], 2) if stats["avg_rating"] else 0,
                    "total_reviews": stats["total_reviews"],
                    "rating_breakdown": {
                        "5_star": stats["five_star"],
                        "4_star": stats["four_star"],
                        "3_star": stats["three_star"],
                        "2_star": stats["two_star"],
                        "1_star": stats["one_star"],
                    },
                },
            })

        except Exception as e:
            print(str(e))
            return Response({"error": f"Failed to retrieve reviews: {str(e)}"}, status=500)




class ReviewDetailView(APIView):
    """
    Get, update or delete a specific review
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, review_id):
        """Get a specific review by ID"""
        from .serializers import ReviewSerializer
        
        try:
            review = Review.objects.get(id=review_id)
            serializer = ReviewSerializer(review, context={'request': request})
            
            # Add ownership flag if user is authenticated
            review_data = serializer.data
            if request.user.is_authenticated:
                review_data['is_my_review'] = (review.review_by.id == request.user.id)
                review_data['can_edit'] = (review.review_by.id == request.user.id)
            
            return Response({
                "review": review_data
            })
        except Review.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)
    
    def put(self, request, review_id):
        """Update a specific review (Only by review author)"""
        from .serializers import ReviewSerializer
        
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)
        
        # Check if the current user is the author of the review
        if review.review_by != request.user:
            return Response({"error": "You can only edit your own reviews"}, status=403)
        
        # Check if user is trying to change the business (not allowed)
        if 'business' in request.data or 'business_id' in request.data:
            return Response({"error": "Cannot change the business for an existing review"}, status=400)
        
        serializer = ReviewSerializer(review, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            updated_review = serializer.save()
            return Response({
                "message": "Review updated successfully",
                "review": ReviewSerializer(updated_review, context={'request': request}).data
            }, status=200)
        
        return Response({"error": serializer.errors}, status=400)
    
    def delete(self, request, review_id):
        """Delete a specific review (Only by review author)"""
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)
        
        # Check if the current user is the author of the review
        if review.review_by != request.user:
            return Response({"error": "You can only delete your own reviews"}, status=403)
        
        business_name = review.business.business_info.company_name if hasattr(review.business, 'business_info') else review.business.full_name
        review.delete()
        
        return Response({
            "message": f"Review for {business_name} deleted successfully"
        }, status=200)


