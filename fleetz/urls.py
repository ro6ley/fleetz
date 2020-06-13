from django.contrib import admin
from django.urls import path, include

from .views import ProfileView, HomeView, ProfileFormView, DisconnectView, UnscheduleTweetView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
    path('profile/', ProfileView.as_view(), name='user_profile'),
    path('disconnect/<int:user_id>/', DisconnectView.as_view(), name="disconnect"),
    path('unschedule/<str:tweet_id>/', UnscheduleTweetView.as_view(), name="unschedule"),
]
