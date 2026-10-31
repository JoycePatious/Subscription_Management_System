from django.conf import settings
from django.db import models
from customers.models import CustomerProfile
from catalog.models import Plan, Product

class QuotationTemplate(models.Model):
    name=models.CharField(max_length=140)
    validity_days=models.PositiveIntegerField(default=14)
    plan=models.ForeignKey(Plan,on_delete=models.PROTECT,null=True,blank=True)
    is_active=models.BooleanField(default=True)
    def __str__(self): return self.name

class Quotation(models.Model):
    class Status(models.TextChoices):
        DRAFT="DRAFT","Draft"; SENT="SENT","Quotation"; ACCEPTED="ACCEPTED","Accepted"; EXPIRED="EXPIRED","Expired"; REJECTED="REJECTED","Rejected"
    number=models.CharField(max_length=40,unique=True)
    customer=models.ForeignKey(CustomerProfile,on_delete=models.PROTECT)
    template=models.ForeignKey(QuotationTemplate,on_delete=models.SET_NULL,null=True,blank=True)
    valid_until=models.DateField()
    status=models.CharField(max_length=12,choices=Status.choices,default=Status.DRAFT)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at=models.DateTimeField(auto_now_add=True)

class QuotationItem(models.Model):
    quotation=models.ForeignKey(Quotation,on_delete=models.CASCADE,related_name="items")
    product=models.ForeignKey(Product,on_delete=models.PROTECT)
    quantity=models.PositiveIntegerField(default=1)
    unit_price=models.DecimalField(max_digits=12,decimal_places=2)
    tax_rate=models.DecimalField(max_digits=5,decimal_places=2,default=0)
