from rest_framework import serializers
from catalog.models import Plan
from .models import Subscription, SubscriptionItem


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    plan_price = serializers.DecimalField(source="plan.price", max_digits=12, decimal_places=2, read_only=True)
    plan_interval = serializers.CharField(source="plan.interval", read_only=True)
    customer_name = serializers.CharField(source="customer.company_name", read_only=True)
    customer_email = serializers.CharField(source="customer.user.email", read_only=True)

    class Meta:
        model = Subscription
        fields = "__all__"


class SubscriptionItemSerializer(serializers.ModelSerializer):
    class Meta: model=SubscriptionItem; fields="__all__"


class PlanChangeRequestSerializer(serializers.Serializer):
    new_plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.filter(is_active=True),
        source="new_plan",
    )


class PlanChangeExecutionSerializer(PlanChangeRequestSerializer):
    immediate_invoice = serializers.BooleanField(default=True)

