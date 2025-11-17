from django.contrib import admin
from .models import Ingredient
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['inci_name', 'purpose', 'created_at']
    search_fields = ['inci_name', 'purpose']
