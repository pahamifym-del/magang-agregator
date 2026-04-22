from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin
from .models import User, SavedInternship


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Tambahkan field custom ke tampilan admin
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Info Tambahan", {"fields": ("avatar_url", "major", "email_notifications")}),
    )
    list_display = ["email", "username", "major", "is_staff", "created_at"]
    search_fields = ["email", "username", "major"]


@admin.register(SavedInternship)
class SavedInternshipAdmin(admin.ModelAdmin):
    list_display = ["user", "internship", "saved_at"]
    search_fields = ["user__email", "internship__title"]