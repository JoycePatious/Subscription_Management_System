from rest_framework import serializers
from .models import Invoice, InvoiceItem, Payment, Tax, Discount
class InvoiceSerializer(serializers.ModelSerializer):
    items=serializers.StringRelatedField(many=True, read_only=True)
    class Meta: model=Invoice; fields="__all__"
class PaymentSerializer(serializers.ModelSerializer):
    class Meta: model=Payment; fields="__all__"
class TaxSerializer(serializers.ModelSerializer):
    class Meta: model=Tax; fields="__all__"
class DiscountSerializer(serializers.ModelSerializer):
    class Meta: model=Discount; fields="__all__"
