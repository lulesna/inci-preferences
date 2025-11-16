from rest_framework import serializers
from .models import Cosmetic
from apps.ingredients.serializers import IngredientSerializer


class CosmeticSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(many=True, read_only=True)

    class Meta:
        model = Cosmetic
        fields = ['id', 'name', 'brand', 'category', 'ingredients', 'created_at']