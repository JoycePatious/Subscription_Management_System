from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("email", "username", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active")
    ordering = ("email",)
    search_fields = ("email", "username")
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Role", {"fields": ("role",)}),
        ("Permissions", {"fields": ("is_active", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2", "role"),
            },
        ),
    )
