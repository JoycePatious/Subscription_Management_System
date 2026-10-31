from django.db import models
from catalog.models import Product
from subscriptions.models import Subscription
from customers.models import CustomerProfile
from decimal import Decimal

class Tax(models.Model):
    name=models.CharField(max_length=100)
    rate=models.DecimalField(max_digits=5,decimal_places=2)
    is_active=models.BooleanField(default=True)

class Discount(models.Model):
    class Kind(models.TextChoices): FIXED="FIXED","Fixed"; PERCENT="PERCENT","Percentage"
    name=models.CharField(max_length=120)
    kind=models.CharField(max_length=10,choices=Kind.choices)
    value=models.DecimalField(max_digits=12,decimal_places=2)
    minimum_quantity=models.PositiveIntegerField(default=1)
    minimum_purchase=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    starts_on=models.DateField(null=True,blank=True)
    ends_on=models.DateField(null=True,blank=True)
    usage_limit=models.PositiveIntegerField(null=True,blank=True)
    usage_count=models.PositiveIntegerField(default=0)
    products=models.ManyToManyField(Product,blank=True)
    applies_to_subscription=models.BooleanField(default=False)
    is_active=models.BooleanField(default=True)

class Invoice(models.Model):
    class Status(models.TextChoices): DRAFT="DRAFT","Draft"; CONFIRMED="CONFIRMED","Confirmed"; PAID="PAID","Paid"; PAYMENT_FAILED="PAYMENT_FAILED","Payment failed"; CANCELLED="CANCELLED","Cancelled"
    number=models.CharField(max_length=40,unique=True)
    customer=models.ForeignKey(CustomerProfile,on_delete=models.PROTECT)
    subscription=models.ForeignKey(Subscription,on_delete=models.PROTECT,related_name="invoices")
    billing_period_start=models.DateField()
    billing_period_end=models.DateField()
    issue_date=models.DateField()
    due_date=models.DateField()
    subtotal=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    discount_total=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    tax_total=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    total=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.DRAFT)
    is_adjustment=models.BooleanField(default=False)
    is_deferred_adjustment=models.BooleanField(default=False)
    first_failed_at=models.DateTimeField(null=True,blank=True)
    grace_period_end=models.DateTimeField(null=True,blank=True)
    first_failure_reason=models.TextField(blank=True)
    dunning_notification_logged_at=models.DateTimeField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=["subscription","billing_period_start","billing_period_end"],condition=models.Q(is_adjustment=False),name="unique_subscription_billing_period")]
        indexes=[models.Index(fields=["status","due_date"])]

class InvoiceItem(models.Model):
    invoice=models.ForeignKey(Invoice,on_delete=models.CASCADE,related_name="items")
    description=models.CharField(max_length=220)
    quantity=models.PositiveIntegerField(default=1)
    unit_price=models.DecimalField(max_digits=12,decimal_places=2)
    tax_rate=models.DecimalField(max_digits=5,decimal_places=2,default=0)
    line_total=models.DecimalField(max_digits=12,decimal_places=2)

class Payment(models.Model):
    invoice=models.ForeignKey(Invoice,on_delete=models.PROTECT,related_name="payments")
    method=models.CharField(max_length=60)
    amount=models.DecimalField(max_digits=12,decimal_places=2)
    paid_on=models.DateField()
    note=models.TextField(blank=True)
    reference=models.CharField(max_length=120,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

class DunningAttempt(models.Model):
    class Status(models.TextChoices):
        PENDING="PENDING","Pending"
        FAILED="FAILED","Failed"
        SUCCEEDED="SUCCEEDED","Succeeded"
        SKIPPED="SKIPPED","Skipped"

    invoice=models.ForeignKey(Invoice,on_delete=models.CASCADE,related_name="dunning_attempts")
    subscription=models.ForeignKey(Subscription,on_delete=models.PROTECT,related_name="dunning_attempts")
    attempt_number=models.PositiveSmallIntegerField()
    attempt_date=models.DateTimeField(null=True,blank=True)
    scheduled_for=models.DateTimeField()
    status=models.CharField(max_length=12,choices=Status.choices,default=Status.PENDING)
    failure_reason=models.TextField(blank=True)
    simulated_gateway_response=models.JSONField(default=dict,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=["attempt_number"]
        constraints=[
            models.UniqueConstraint(fields=["invoice","attempt_number"],name="unique_invoice_dunning_attempt"),
            models.CheckConstraint(condition=models.Q(attempt_number__gte=1,attempt_number__lte=3),name="dunning_attempt_number_range"),
        ]
