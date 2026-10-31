from rest_framework import serializers
from .models import DunningAttempt, Invoice, InvoiceItem, Payment, Tax, Discount


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = "__all__"


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.company_name", read_only=True)
    customer_email = serializers.CharField(source="customer.user.email", read_only=True)
    subscription_number = serializers.CharField(source="subscription.number", read_only=True)
    plan_name = serializers.CharField(source="subscription.plan.name", read_only=True)

    class Meta:
        model = Invoice
        fields = "__all__"


class DunningAttemptSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source="invoice.number", read_only=True)
    subscription_status = serializers.CharField(source="subscription.status", read_only=True)

    class Meta:
        model = DunningAttempt
        fields = (
            "id",
            "attempt_number",
            "attempt_date",
            "scheduled_for",
            "status",
            "failure_reason",
            "simulated_gateway_response",
            "invoice_number",
            "subscription_status",
        )


class PaymentFailureSerializer(serializers.Serializer):
    reason = serializers.CharField(allow_blank=False)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta: model=Payment; fields="__all__"
class TaxSerializer(serializers.ModelSerializer):
    class Meta: model=Tax; fields="__all__"
class DiscountSerializer(serializers.ModelSerializer):
    class Meta: model=Discount; fields="__all__"
