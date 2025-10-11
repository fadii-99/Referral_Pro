from django.urls import path
from .views import (
    SignupView, 
    EmailPasswordLoginView,
    SocialLoginView,
    SendOTPView,
    VerifyOTPView,
    CreateNewPasswordView,
    DeleteUsersByIdsView,
    LogoutView,
    UserInfoView,
    EmployeeManagementView,
    SendResetPasswordView,
    TestEmployeeManagementView,
    UpdateUserView,
    SetEmployeePasswordView,
    ResetPasswordView,
    AccountDeletionView,
    checkEmailExistsView,
    RegisterFCMTokenView,
    UnregisterFCMTokenView,
    # Review views
    ReviewManagementView,
    BusinessReviewsView,
    ReviewDetailView,
)



urlpatterns = [
    # Basic auth endpoints
    path('sign_up/', SignupView.as_view(), name='signup'),
    path('login/', EmailPasswordLoginView.as_view(), name='login'),
    path('social_login/', SocialLoginView.as_view(), name='social_login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Password reset flow
    path('send_otp/', SendOTPView.as_view(), name='send_otp'),
    path('verify_otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('reset_password/', CreateNewPasswordView.as_view(), name='reset_password'),
    path('check_email/', checkEmailExistsView.as_view(), name='get_user'),

    path('get_user/', UserInfoView.as_view(), name='get_user'),
    path('update_user/', UpdateUserView.as_view(), name='update_user'),

    path('employees/', EmployeeManagementView.as_view(), name='send_invite'),
    path('employees_post/', TestEmployeeManagementView.as_view(), name='send_invite'),
    path('set_employee_password/', SetEmployeePasswordView.as_view(), name='set-employee-password'),
    path('employee_reset_password/', SendResetPasswordView.as_view(), name='send_reset_password'),

    # Delete user by email
    path('delete/', DeleteUsersByIdsView.as_view(), name='delete_user'),
    path('update_password/', ResetPasswordView.as_view(), name='update_password'),
    path('account_deletion/', AccountDeletionView.as_view(), name='account_deletion'),

    # Social auth endpoints
    path('facebook/callback/<str:code>/', SocialLoginView.as_view(), name='facebook_login'),

    path("push/register/", RegisterFCMTokenView.as_view()),
    path("push/unregister/", UnregisterFCMTokenView.as_view()),

    

]
