from rest_framework import serializers
from .models import CustomerProfile
class CustomerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True, required=False)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = CustomerProfile
        fields = "__all__"
        read_only_fields = ("user",)

    def create(self, validated_data):
        email = validated_data.pop("email", None)
        request = self.context.get("request")
        user = None
        if email:
            from accounts.models import User
            user, _ = User.objects.get_or_create(
                email=email.lower().strip(),
                defaults={"role": User.Role.CUSTOMER}
            )
            profile, created = CustomerProfile.objects.get_or_create(user=user, defaults=validated_data)
            if not created:
                for k, v in validated_data.items():
                    setattr(profile, k, v)
                profile.save()
            return profile
        elif request and request.user.is_authenticated and request.user.role == "CUSTOMER":
            user = request.user
            profile, _ = CustomerProfile.objects.get_or_create(user=user, defaults=validated_data)
            return profile
        return super().create(validated_data)
