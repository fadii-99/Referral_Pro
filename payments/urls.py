from django.urls import path
from . import views

urlpatterns = [
	path('test/', views.test_page, name='payments_test'),
	path('connect/stripe/start/', views.connect_start, name='connect_start'),
	path('connect/stripe/callback/', views.connect_callback, name='connect_callback'),
	path('account_links/create/', views.create_account_link, name='create_account_link'),
	path('withdrawals/', views.create_withdrawal, name='create_withdrawal'),
	path('webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'),
]
