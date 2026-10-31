from django.conf import settings
from django.db import models

class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile")
    company_name = models.CharField(max_length=180, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    billing_address = models.TextField(blank=True)
    tax_identifier = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.company_name or self.user.email
