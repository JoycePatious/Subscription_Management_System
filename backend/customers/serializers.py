from rest_framework import serializers
from .models import CustomerProfile
class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = "__all__"
        read_only_fields = ("user",)
