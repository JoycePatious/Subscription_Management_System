from rest_framework import serializers
from .models import Product, ProductVariant, Plan
class ProductSerializer(serializers.ModelSerializer):
    class Meta: model=Product; fields="__all__"
class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta: model=ProductVariant; fields="__all__"
class PlanSerializer(serializers.ModelSerializer):
    class Meta: model=Plan; fields="__all__"
