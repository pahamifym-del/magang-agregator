from django.contrib import admin
from .models import ScraperConfig


@admin.register(ScraperConfig)
class ScraperConfigAdmin(admin.ModelAdmin):
    list_display = ["source", "is_active", "interval_minutes", "max_pages", "updated_at"]
    list_filter = ["is_active"]