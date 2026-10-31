from rest_framework.routers import DefaultRouter
from .views import InvoiceViewSet, PaymentViewSet, TaxViewSet, DiscountViewSet
router=DefaultRouter()
router.register("invoices",InvoiceViewSet); router.register("payments",PaymentViewSet)
router.register("taxes",TaxViewSet); router.register("discounts",DiscountViewSet)
urlpatterns=router.urls
