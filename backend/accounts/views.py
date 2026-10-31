from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .emails import send_password_reset_email
from .models import User
from .permissions import IsAdmin
from .serializers import (
    EmailTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    StaffCreateSerializer,
    UserSerializer,
)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailTokenObtainPairSerializer


class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class StaffCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = StaffCreateSerializer
    permission_classes = [IsAdmin]


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data["email"]).first()
        if user is not None:
            send_password_reset_email(user)
        return Response(
            {"detail": "If an account exists for this email, a reset token has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password has been reset."}, status=status.HTTP_200_OK)
