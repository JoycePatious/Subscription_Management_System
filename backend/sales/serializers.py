from rest_framework import serializers
from .models import Quotation, QuotationTemplate, QuotationItem
class QuotationSerializer(serializers.ModelSerializer):
    class Meta: model=Quotation; fields="__all__"; read_only_fields=("created_by",)
class QuotationTemplateSerializer(serializers.ModelSerializer):
    class Meta: model=QuotationTemplate; fields="__all__"
