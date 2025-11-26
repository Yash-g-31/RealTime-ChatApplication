from django.urls import path
from .views import (
    RegisterView,
    CurrentUserView,
    UserListView,
    UserPresenceView,
    RateLimitedTokenObtainPairView,
)
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path("register-x92jf03/", RegisterView.as_view(), name="register"),

    path("login/", RateLimitedTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    path("me/", CurrentUserView.as_view(), name="me"),
    path("users/", UserListView.as_view(), name="user"),

    path("presence/", UserPresenceView.as_view()),
]
