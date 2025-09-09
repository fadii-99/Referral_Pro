# referr/urls.py
from django.urls import path
from .views import CompaniesListView, SendReferralView, ListReferralView,ListCompanyReferralView

urlpatterns = [
    path("companies_list/", CompaniesListView.as_view(), name="companies_list"),
    path("send_referral/", SendReferralView.as_view(), name="send_referral"),
    path("list_solo_referral/", ListReferralView.as_view(), name="list_referral"),
    path("list_company_referral/", ListCompanyReferralView.as_view(), name="list_company_referral"),
]
