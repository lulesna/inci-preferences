from rest_framework import serializers
from .models import Cosmetic
from apps.ingredients.serializers import IngredientSerializer


class CosmeticSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(many=True, read_only=True)
    full_category = serializers.CharField(source='get_full_category', read_only=True)
    ingredients_text = serializers.CharField(write_only=True, required=False, allow_blank=True)

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
            'ingredients_text',
            'created_at'
        ]


class CosmeticWithSafetySerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(many=True, read_only=True)
    full_category = serializers.CharField(source='get_full_category', read_only=True)
    safety_color = serializers.SerializerMethodField()

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
            'safety_color',
            'created_at'
        ]

    def get_safety_color(self, obj):
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            return 'UNKNOWN'

        try:
            profile = request.user.profile
            return profile.get_cosmetic_safety_color(obj)
        except:
            return 'UNKNOWN'
