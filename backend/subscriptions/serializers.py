from rest_framework import serializers
from .models import Subscription, SubscriptionItem
class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta: model=Subscription; fields="__all__"
class SubscriptionItemSerializer(serializers.ModelSerializer):
    class Meta: model=SubscriptionItem; fields="__all__"
