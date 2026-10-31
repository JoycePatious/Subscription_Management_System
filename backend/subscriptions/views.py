from django.core.exceptions import ValidationError
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.mixins import CustomerOwnedQuerysetMixin
from accounts.permissions import SubscriptionPlanChangePermission
from billing.serializers import InvoiceSerializer
from .models import Subscription
from .serializers import (
    PlanChangeExecutionSerializer,
    PlanChangeRequestSerializer,
    SubscriptionSerializer,
)
from .services.proration_service import apply_plan_change, calculate_proration


class SubscriptionViewSet(CustomerOwnedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Subscription.objects.select_related("customer", "plan").prefetch_related("items").all()
    serializer_class = SubscriptionSerializer
    permission_classes = [SubscriptionPlanChangePermission]
    customer_user_field = "customer__user"

    @action(detail=True, methods=["post"], url_path="preview-proration")
    def preview_proration(self, request, pk=None):
        subscription = self.get_object()
        payload = PlanChangeRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            breakdown = calculate_proration(subscription, payload.validated_data["new_plan"])
        except ValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        return Response(breakdown)

    @action(detail=True, methods=["post"], url_path="change-plan")
    def change_plan(self, request, pk=None):
        subscription = self.get_object()
        payload = PlanChangeExecutionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            updated_subscription, invoice, breakdown = apply_plan_change(
                subscription,
                payload.validated_data["new_plan"],
                payload.validated_data.get("immediate_invoice", True),
            )
        except ValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        return Response(
            {
                "subscription": SubscriptionSerializer(updated_subscription).data,
                "invoice": InvoiceSerializer(invoice).data,
                "proration": breakdown,
            },
            status=status.HTTP_200_OK,
        )
