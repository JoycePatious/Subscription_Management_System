from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("customers.urls")),
    path("api/", include("catalog.urls")),
    path("api/", include("sales.urls")),
    path("api/", include("subscriptions.urls")),
    path("api/", include("billing.urls")),
    path("api/", include("reports.urls")),
]
