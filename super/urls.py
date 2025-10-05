from django.urls import path
from .views import adminDashboardView, LoadUsersView

urlpatterns = [
    path('dashboard/', adminDashboardView.as_view(), name='super-admin-dashboard'),
    path('users/', LoadUsersView.as_view(), name='load-users'),
]
