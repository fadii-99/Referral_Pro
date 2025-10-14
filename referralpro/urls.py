"""
URL configuration for referralpro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from activity.views import ActivityListView, ReferralActivityListView
from chat import views as views1
from accounts import views as views2


urlpatterns = [
    path('auth/', include('accounts.urls')),
    path('refer/', include('referr.urls')),
    path('chat/', include('chat.urls')),
    path('super/', include('super.urls')),
    path("activity/", ReferralActivityListView.as_view(), name="referral_activity_list"),
    path("all_activity/", ActivityListView.as_view(), name="activity_list"),

    path('notifications/', views1.NotificationListView.as_view(), name='notification_list'),
    path('notifications/mark-read/', views1.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('notifications/stats/', views1.NotificationStatsView.as_view(), name='notification_stats'),

    # Review endpoints
    path('reviews/', views2.ReviewManagementView.as_view(), name='review_management'),  # GET (list), POST (create), PUT (update), DELETE
    path('business/<int:business_id>/reviews/', views2.BusinessReviewsView.as_view(), name='business_reviews'),  # GET all reviews for a business

    # path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
