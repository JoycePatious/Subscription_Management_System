from rest_framework import serializers
from .models import DunningAttempt, Invoice, InvoiceItem, Payment, Tax, Discount


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = "__all__"


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = "__all__"


class DunningAttemptSerializer(serializers.ModelSerializer):
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
        )


class PaymentFailureSerializer(serializers.Serializer):
    reason = serializers.CharField(allow_blank=False)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta: model=Payment; fields="__all__"
class TaxSerializer(serializers.ModelSerializer):
    class Meta: model=Tax; fields="__all__"
class DiscountSerializer(serializers.ModelSerializer):
    class Meta: model=Discount; fields="__all__"
