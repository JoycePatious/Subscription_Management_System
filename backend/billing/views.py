from django.core.exceptions import ValidationError
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.mixins import CustomerOwnedQuerysetMixin
from accounts.permissions import IsAdminOrStaff, IsAdminOrStaffOrCustomerReadOwn
from .models import DunningAttempt, Invoice, Payment, Tax, Discount
from .serializers import (
    DunningAttemptSerializer,
    InvoiceSerializer,
    PaymentFailureSerializer,
    PaymentSerializer,
    TaxSerializer,
    DiscountSerializer,
)
from .services.dunning_service import execute_dunning_retry, process_payment_failure


class InvoiceViewSet(CustomerOwnedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Invoice.objects.select_related("customer", "subscription").prefetch_related(
        "items", "payments", "dunning_attempts"
    ).all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAdminOrStaffOrCustomerReadOwn]
    customer_user_field = "customer__user"

    @action(detail=True, methods=["post"], url_path="record-failure", permission_classes=[IsAdminOrStaff])
    def record_failure(self, request, pk=None):
        invoice = self.get_object()
        payload = PaymentFailureSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            invoice = process_payment_failure(invoice, payload.validated_data["reason"])
        except ValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        except ValueError as error:
            raise serializers.ValidationError({"detail": str(error)}) from error
        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="retry-payment", permission_classes=[IsAdminOrStaff])
    def retry_payment(self, request, pk=None):
        invoice = self.get_object()
        gateway_response = None
        if request.data.get("simulate_success") is True or request.data.get("simulate_outcome") == "succeeded":
            gateway_response = {"status": "succeeded", "source": "simulated_gateway", "reference": "SIM_SUCC_001"}
        elif request.data.get("simulate_failure") is True or request.data.get("simulate_outcome") == "failed":
            gateway_response = {"status": "failed", "reason": request.data.get("reason", "Card declined by issuing bank")}
        elif "gateway_response" in request.data:
            gateway_response = request.data["gateway_response"]

        try:
            attempt = execute_dunning_retry(invoice, gateway_response=gateway_response, force=True)
        except ValueError as error:
            raise serializers.ValidationError({"detail": str(error)}) from error
        if attempt is None:
            return Response(InvoiceSerializer(invoice).data, status=status.HTTP_200_OK)
        return Response(DunningAttemptSerializer(attempt).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="dunning-history")
    def dunning_history(self, request, pk=None):
        invoice = self.get_object()
        attempts = DunningAttempt.objects.filter(invoice=invoice).order_by("attempt_number")
        return Response(DunningAttemptSerializer(attempts, many=True).data)


class PaymentViewSet(CustomerOwnedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("invoice").all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminOrStaffOrCustomerReadOwn]
    customer_user_field = "invoice__customer__user"


class TaxViewSet(viewsets.ModelViewSet):
    queryset = Tax.objects.all()
    serializer_class = TaxSerializer
    permission_classes = [IsAdminOrStaff]


class DiscountViewSet(viewsets.ModelViewSet):
    queryset = Discount.objects.prefetch_related("products").all()
    serializer_class = DiscountSerializer
    permission_classes = [IsAdminOrStaff]
