from rest_framework import viewsets
from accounts.mixins import CustomerOwnedQuerysetMixin
from accounts.permissions import IsAdminOrStaff, IsAdminOrStaffOrCustomerReadOwn
from .models import Invoice, Payment, Tax, Discount
from .serializers import InvoiceSerializer, PaymentSerializer, TaxSerializer, DiscountSerializer


class InvoiceViewSet(CustomerOwnedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Invoice.objects.select_related("customer", "subscription").prefetch_related("items", "payments").all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAdminOrStaffOrCustomerReadOwn]
    customer_user_field = "customer__user"


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
