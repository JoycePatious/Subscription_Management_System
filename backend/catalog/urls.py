from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, VariantViewSet, PlanViewSet
router=DefaultRouter()
router.register("products",ProductViewSet); router.register("variants",VariantViewSet); router.register("plans",PlanViewSet)
urlpatterns=router.urls
