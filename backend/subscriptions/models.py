from django.db import models
from customers.models import CustomerProfile
from catalog.models import Plan, Product

class Subscription(models.Model):
    class Status(models.TextChoices):
        DRAFT="DRAFT","Draft"; QUOTATION="QUOTATION","Quotation"; CONFIRMED="CONFIRMED","Confirmed"; ACTIVE="ACTIVE","Active"; PAST_DUE="PAST_DUE","Past due"; IN_GRACE_PERIOD="IN_GRACE_PERIOD","In grace period"; SUSPENDED="SUSPENDED","Suspended"; CANCELED="CANCELED","Canceled"; PAUSED="PAUSED","Paused"; CLOSED="CLOSED","Closed"
    number=models.CharField(max_length=40,unique=True)
    customer=models.ForeignKey(CustomerProfile,on_delete=models.PROTECT,related_name="subscriptions")
    plan=models.ForeignKey(Plan,on_delete=models.PROTECT)
    start_date=models.DateField()
    expiry_date=models.DateField(null=True,blank=True)
    next_billing_date=models.DateField(null=True,blank=True,db_index=True)
    payment_terms=models.CharField(max_length=160,blank=True)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.DRAFT,db_index=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.number

class SubscriptionItem(models.Model):
    subscription=models.ForeignKey(Subscription,on_delete=models.CASCADE,related_name="items")
    product=models.ForeignKey(Product,on_delete=models.PROTECT)
    quantity=models.PositiveIntegerField(default=1)
    unit_price=models.DecimalField(max_digits=12,decimal_places=2)
    tax_rate=models.DecimalField(max_digits=5,decimal_places=2,default=0)
