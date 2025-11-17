from django.contrib import admin
from .models import Cosmetic

from django.contrib import admin
from .models import Cosmetic


@admin.register(Cosmetic)
class CosmeticAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'main_category', 'subcategory', 'product_type', 'created_at']
    search_fields = ['name', 'brand']
    list_filter = ['main_category', 'subcategory', 'product_type']
    filter_horizontal = ['ingredients']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'brand')
        }),
        ('Categories', {
            'fields': ('main_category', 'subcategory', 'product_type'),
            'description': 'Main: Face/Makeup/Body/Hands. For Face: select subcategory. For Makeup: select area (subcategory) and product type.'
        }),
        ('Ingredients', {
            'fields': ('ingredients',)
        }),
    )
