from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from accounts.mixins import CustomerOwnedQuerysetMixin
from accounts.permissions import IsAdminOrStaff
from .models import CustomerProfile
from .serializers import CustomerProfileSerializer


class CustomerViewSet(CustomerOwnedQuerysetMixin, viewsets.ModelViewSet):
    queryset = CustomerProfile.objects.select_related("user").all()
    serializer_class = CustomerProfileSerializer
    customer_user_field = "user"

    def get_permissions(self):
        if self.action in ("create", "destroy"):
            return [IsAdminOrStaff()]
        return [IsAuthenticated()]
