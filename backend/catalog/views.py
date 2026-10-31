from rest_framework import viewsets
from accounts.permissions import IsAdminOrReadOnly
from .models import Product, ProductVariant, Plan
from .serializers import ProductSerializer, ProductVariantSerializer, PlanSerializer
class ProductViewSet(viewsets.ModelViewSet):
    queryset=Product.objects.prefetch_related("variants").all(); serializer_class=ProductSerializer; permission_classes=[IsAdminOrReadOnly]
class VariantViewSet(viewsets.ModelViewSet):
    queryset=ProductVariant.objects.select_related("product").all(); serializer_class=ProductVariantSerializer; permission_classes=[IsAdminOrReadOnly]
class PlanViewSet(viewsets.ModelViewSet):
    queryset=Plan.objects.all(); serializer_class=PlanSerializer; permission_classes=[IsAdminOrReadOnly]
