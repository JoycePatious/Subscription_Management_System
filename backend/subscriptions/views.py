from rest_framework import viewsets
from accounts.mixins import CustomerOwnedQuerysetMixin
from accounts.permissions import IsAdminOrStaffOrCustomerReadOwn
from .models import Subscription
from .serializers import SubscriptionSerializer


class SubscriptionViewSet(CustomerOwnedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Subscription.objects.select_related("customer", "plan").prefetch_related("items").all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAdminOrStaffOrCustomerReadOwn]
    customer_user_field = "customer__user"
