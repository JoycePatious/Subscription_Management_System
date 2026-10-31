from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "username", "role")
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "username", "password")
        extra_kwargs = {
            "username": {"required": False, "allow_blank": True},
            "email": {"required": True},
        }

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        username = validated_data.pop("username", None) or None
        extra = {"role": User.Role.CUSTOMER}
        if username:
            extra["username"] = username
        return User.objects.create_user(**validated_data, **extra)


class StaffCreateSerializer(RegisterSerializer):
    """Admin-only. Always creates STAFF; role cannot be sent by the client."""

    def create(self, validated_data):
        username = validated_data.pop("username", None) or None
        extra = {"role": User.Role.STAFF}
        if username:
            extra["username"] = username
        return User.objects.create_user(**validated_data, **extra)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        return value.lower().strip()

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        email = attrs["email"]
        token = attrs["token"]
        user = User.objects.filter(email=email).first()
        if user is None or not default_token_generator.check_token(user, token):
            raise serializers.ValidationError("Invalid or expired reset token.")
        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["password"])
        user.save()
        return user
