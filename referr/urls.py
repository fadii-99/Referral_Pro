# referr/urls.py
from django.urls import path

from .views import ListCompaniesView, SendReferralView,ListSoloReferralView, ListReferralView,ListCompanyReferralView, SendAppInvitationView, ListAssignedReferralView,CompleteReferralView, AssignRepView, ListRepReferralView, SendAcceptView, UpdateReferralPrivacyView, FavoriteCompanyView, DashboardStatsView

urlpatterns = [
    path("dashboard/", DashboardStatsView.as_view(), name="companies_list"),
    path("companies_list/", ListCompaniesView.as_view(), name="companies_list"),
    path("list_referral/", ListReferralView.as_view(), name="list_referral"),
    path("send_referral/", SendReferralView.as_view(), name="send_referral"),
    path("accept_referral/", SendAcceptView.as_view(), name="accept_referral"),
    path("list_solo_referral/",  ListSoloReferralView.as_view(), name="list_solo_referral"),
    path("update_referral_privacy/", UpdateReferralPrivacyView.as_view(), name="list_solo_referral"),
    path("list_company_referral/", ListCompanyReferralView.as_view(), name="list_company_referral"),
    path("list_rep_referral/", ListRepReferralView.as_view(), name="list_rep_referral"),
    path("list_assigned_referral/", ListAssignedReferralView.as_view(), name="list_assigned_referral"),
    path("assign_rep/", AssignRepView.as_view(), name="list_assigned_referral"),
    path("complete_referral/", CompleteReferralView.as_view(), name="send_referral"),
    path("add_manually/", SendAppInvitationView.as_view(), name="add_manually"),
    path('favorite/', FavoriteCompanyView.as_view(), name='add_favorite'),

]
