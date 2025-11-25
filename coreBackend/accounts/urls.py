from django.urls import path
from .views import RegisterView, CurrentUserView, UserListView, UserPresenceView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path("register-x92jf03/", RegisterView.as_view(), name="register"),

    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    path("me/", CurrentUserView.as_view(), name="me"),
    path("users/", UserListView.as_view(), name="user"),

    path("presence/", UserPresenceView.as_view()),
]
