from django.contrib import admin
from .models import Ingredient
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'inci_name', 'created_at']
    search_fields = ['name', 'inci_name']
