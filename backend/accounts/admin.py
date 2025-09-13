from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            None,
            {
                "fields": (
                    "role",
                    "phone_number",
                    "location",
                    "profile_picture",
                )
            },
        ),
    )
    list_display = (
        "username",
        "email",
        "role",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "email", "phone_number", "location")
