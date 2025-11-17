from rest_framework import serializers
from .models import Cosmetic
from apps.ingredients.serializers import IngredientSerializer


class CosmeticSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(many=True, read_only=True)
    full_category = serializers.CharField(source='get_full_category', read_only=True)

    class Meta:
        model = Cosmetic
        fields = [
            'id',
            'name',
            'brand',
            'main_category',
            'subcategory',
            'product_type',
            'full_category',
            'ingredients',
            'created_at'
        ]