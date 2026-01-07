from django.contrib import admin
from django.contrib import messages
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
        ('Ingredients - Option 1: Paste full list', {
            'fields': ('ingredients_text',),
            'description': 'Paste the full INCI ingredients list (comma-separated). Click Save to auto-match ingredients.'
        }),
        ('Ingredients - Option 2: Select manually', {
            'fields': ('ingredients',),
            'classes': ('collapse',),
        }),
    )

    def get_ingredients_count(self, obj):
        return obj.ingredients.count()

    get_ingredients_count.short_description = 'Ingredients'

    def get_ingredients_count(self, obj):
        return obj.ingredients.count()

    get_ingredients_count.short_description = 'Ingredients'

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        obj = form.instance
        if obj.ingredients_text:
            result = obj.parse_and_add_ingredients(auto_create=True)

            if result['matched']:
                messages.success(
                    request,
                    f"Matched {len(result['matched'])} ingredients"
                )

            if result['not_found']:
                messages.warning(
                    request,
                    f"Not found: {', '.join(result['not_found'][:5])}"
                )
