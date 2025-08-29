from django.urls import path
from .views import (
    SignupView, 
    EmailPasswordLoginView,
    SocialLoginView,
    SendOTPView,
    VerifyOTPView,
    CreateNewPasswordView
)

urlpatterns = [
    # Basic auth endpoints
    path('sign_up/', SignupView.as_view(), name='signup'),
    path('login/', EmailPasswordLoginView.as_view(), name='login'),
    path('social_login/', SocialLoginView.as_view(), name='social_login'),
    
    # Password reset flow
    path('send_otp/', SendOTPView.as_view(), name='send_otp'),
    path('verify_otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('reset_password/', CreateNewPasswordView.as_view(), name='reset_password'),

    # Social auth endpoints
    # path('google/', GoogleLoginView.as_view(), name='google_login'),
    # path('facebook/', FacebookLoginView.as_view(), name='facebook_login'),
    # path('apple/', AppleLoginView.as_view(), name='apple_login'),
]
