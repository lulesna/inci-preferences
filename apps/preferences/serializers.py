from rest_framework import serializers
from .models import UserProfile
from apps.ingredients.serializers import IngredientSerializer


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    allergic_to = IngredientSerializer(many=True, read_only=True)
    avoided_ingredients = IngredientSerializer(many=True, read_only=True)
    preferred_ingredients = IngredientSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'username',
            'allergic_to',
            'avoided_ingredients',
            'preferred_ingredients',
            'skin_type',
            'skin_concerns',
            'vegan_only',
            'cruelty_free_only',
            'fragrance_free',
            'updated_at'
        ]
