from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .models import Profile
from chat.models import Message
from rest_framework_simplejwt.views import TokenObtainPairView


class RateLimitedTokenObtainPairView(TokenObtainPairView):
    """
    JWT login view with per-IP rate limiting.
    Used at /api/login/
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        # Rate limit: max 5 login attempts per 60 seconds per IP
        if rate_limit(request, action="login", limit=5, window_seconds=60):
            return Response(
                {"detail": "Too many login attempts. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Call the original SimpleJWT logic
        return super().post(request, *args, **kwargs)

def rate_limit(request, action: str, limit: int, window_seconds: int = 60) -> bool:
    """
    Simple per-IP rate limiter using Django cache.

    action: "login", "register", "send_message", etc.
    limit:  allowed attempts within window_seconds per IP.
    returns True if blocked, False if allowed.
    """
    ip = request.META.get("REMOTE_ADDR", "unknown")
    key = f"rl:{action}:{ip}"

    attempts = cache.get(key, 0)

    if attempts >= limit:
        return True  # blocked

    cache.set(key, attempts + 1, timeout=window_seconds)
    return False


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]  # still public, but protected by secret

    def post(self, request):
        # 🔹 Rate limit: max 3 registrations per minute per IP
        if rate_limit(request, action="register", limit=3, window_seconds=60):
            return Response(
                {"detail": "Too many registration attempts. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # 1) Check secret key
        secret = request.data.get("secret")
        if secret != settings.REGISTRATION_SECRET:
            return Response(
                {"detail": "Invalid registration secret."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 2) Normal registration flow
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # 🔹 Rate limit: max 5 login attempts per minute per IP
        if rate_limit(request, action="login", limit=5, window_seconds=60):
            return Response(
                {"detail": "Too many login attempts. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        current_user = request.user
        others = User.objects.exclude(id=current_user.id)

        result = []

        for user in others:
            # Get last message between current_user and this user
            last_msg = (
                Message.objects.filter(
                    sender__in=[current_user, user],
                    receiver__in=[current_user, user],
                )
                .order_by("-timestamp")
                .first()
            )

            if last_msg:
                text = last_msg.content
                if len(text) > 40:
                    text = text[:40] + "…"

                last_message = text
                last_message_time = last_msg.timestamp
            else:
                last_message = ""
                last_message_time = None

            result.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "last_message": last_message,
                    "last_message_time": last_message_time,
                }
            )

        return Response(result, status=200)


class UserPresenceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        users = User.objects.exclude(id=request.user.id)
        data = []

        now = timezone.now()

        for user in users:
            profile, _ = Profile.objects.get_or_create(user=user)
            last_seen = profile.last_seen

            if last_seen:
                seconds = (now - last_seen).total_seconds()
                online = seconds < 60  # 1 minute window
            else:
                online = False

            data.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "online": online,
                    "last_seen": last_seen,
                }
            )

        return Response(data, status=200)
