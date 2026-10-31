from rest_framework import serializers
from catalog.models import Plan
from .models import Subscription, SubscriptionItem


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta: model=Subscription; fields="__all__"


class SubscriptionItemSerializer(serializers.ModelSerializer):
    class Meta: model=SubscriptionItem; fields="__all__"


class PlanChangeRequestSerializer(serializers.Serializer):
    new_plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.filter(is_active=True),
        source="new_plan",
    )


class PlanChangeExecutionSerializer(PlanChangeRequestSerializer):
    immediate_invoice = serializers.BooleanField(default=True)

