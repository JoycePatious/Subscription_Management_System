from rest_framework.routers import DefaultRouter
from .views import QuotationViewSet, QuotationTemplateViewSet
router=DefaultRouter(); router.register("quotations",QuotationViewSet); router.register("quotation-templates",QuotationTemplateViewSet)
urlpatterns=router.urls
