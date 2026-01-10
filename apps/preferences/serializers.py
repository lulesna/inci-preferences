from rest_framework import serializers
from .models import UserProfile
from apps.ingredients.serializers import IngredientSerializer


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    safe_ingredients = IngredientSerializer(many=True, read_only=True)
    moderate_ingredients = IngredientSerializer(many=True, read_only=True)
    unsafe_ingredients = IngredientSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'username',
            'safe_ingredients',
            'moderate_ingredients',
            'unsafe_ingredients',
            'updated_at'
        ]

class UpdatePreferencesSerializer(serializers.Serializer):
    ingredient_id = serializers.IntegerField()
    color = serializers.ChoiceField(choices=['GREEN', 'YELLOW', 'RED', 'NONE'])
