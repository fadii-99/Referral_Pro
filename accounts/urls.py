from django.urls import path
from .views import (
    SignupView, 
    EmailPasswordLoginView,
    SocialLoginView,
    SendOTPView,
    VerifyOTPView,
    CreateNewPasswordView,
    DeleteUserView,
    LogoutView,
    UserInfoView,
    EmployeeManagementView,
    SendResetPasswordView,
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

    path('get_user/', UserInfoView.as_view(), name='get_user'),

    path('employees/', EmployeeManagementView.as_view(), name='send_invite'),
    path('employee_reset_password/<int:id>/', SendResetPasswordView.as_view(), name='send_reset_password'),
    # path('set_password/', SetEmployeePasswordView.as_view(), name='set_password'),
    # path('employee_list/', ListEmployeesView.as_view(), name='employee_list'),
    # path('edit_employee/', EditEmployeeView.as_view(), name='edit_employee'),
    # path('delete_employee/', DeleteEmployeeView.as_view(), name='delete_employee'),

    # Delete user by email
    path('delete/<int:id>/', DeleteUserView.as_view(), name='delete_user'),

    # Social auth endpoints
    # path('google/', GoogleLoginView.as_view(), name='google_login'),
    # path('facebook/', FacebookLoginView.as_view(), name='facebook_login'),
    # path('apple/', AppleLoginView.as_view(), name='apple_login'),
]
