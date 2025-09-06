# referr/urls.py
from django.urls import path
from .views import CompaniesListView, SendReferralView

urlpatterns = [
    path("companies/", CompaniesListView.as_view(), name="companies_list"),
    path("send/", SendReferralView.as_view(), name="send_referral"),
]
