from django.contrib import admin
from django.urls import path, include

import fleetz.views as views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
    path('profile/', views.ProfileView.as_view(), name='user_profile'),
    path('schedule/', views.ScheduleView.as_view(), name='schedule_tweet'),
    path('disconnect/<int:user_id>/', views.DisconnectView.as_view(), name="disconnect"),
    path('unschedule/<str:tweet_id>/', views.UnscheduleTweetView.as_view(), name="unschedule"),
]
