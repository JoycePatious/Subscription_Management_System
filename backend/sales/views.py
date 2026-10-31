from rest_framework import viewsets
from accounts.permissions import IsAdminOrStaff, IsAdmin
from .models import Quotation, QuotationTemplate
from .serializers import QuotationSerializer, QuotationTemplateSerializer
class QuotationViewSet(viewsets.ModelViewSet):
    queryset=Quotation.objects.select_related("customer","template").prefetch_related("items").all()
    serializer_class=QuotationSerializer; permission_classes=[IsAdminOrStaff]
    def perform_create(self, serializer): serializer.save(created_by=self.request.user)
class QuotationTemplateViewSet(viewsets.ModelViewSet):
    queryset=QuotationTemplate.objects.all(); serializer_class=QuotationTemplateSerializer; permission_classes=[IsAdmin]
