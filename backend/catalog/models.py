from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Product(models.Model):
    name = models.CharField(max_length=160)
    product_type = models.CharField(max_length=80)
    sales_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=100)
    price_delta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    def __str__(self): return f"{self.product.name} - {self.name}"

class Plan(models.Model):
    class Interval(models.TextChoices):
        DAILY="DAILY","Daily"; WEEKLY="WEEKLY","Weekly"; MONTHLY="MONTHLY","Monthly"; YEARLY="YEARLY","Yearly"
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    interval = models.CharField(max_length=10, choices=Interval.choices)
    minimum_quantity = models.PositiveIntegerField(default=1)
    available_from = models.DateField(null=True, blank=True)
    available_until = models.DateField(null=True, blank=True)
    allow_pause = models.BooleanField(default=False)
    allow_early_close = models.BooleanField(default=False)
    allow_renewal = models.BooleanField(default=True)
    auto_close = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name
