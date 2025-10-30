from django.contrib import admin
from .models import Cosmetic

@admin.register(Cosmetic)
class CosmeticAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'created_at']
    search_fields = ['name', 'brand']
    list_filter = ['category']
