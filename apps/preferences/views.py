from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserProfile
from .serializers import UserProfileSerializer, UpdatePreferencesSerializer
from apps.ingredients.models import Ingredient


class UserPreferencesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        try:
            profile = request.user.profile
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({
                'error': 'Profile not found.'
            }, status=404)

    @action(detail=False, methods=['post'])
    def set_ingredient_color(self, request):
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)

        serializer = UpdatePreferencesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ingredient_id = serializer.validated_data['ingredient_id']
        color = serializer.validated_data['color']

        try:
            ingredient = Ingredient.objects.get(id=ingredient_id)
        except Ingredient.DoesNotExist:
            return Response({
                'error': 'Ingredient not found'
            }, status=status.HTTP_404_NOT_FOUND)

        profile.safe_ingredients.remove(ingredient)
        profile.moderate_ingredients.remove(ingredient)
        profile.unsafe_ingredients.remove(ingredient)

        if color == 'GREEN':
            profile.safe_ingredients.add(ingredient)
        elif color == 'YELLOW':
            profile.moderate_ingredients.add(ingredient)
        elif color == 'RED':
            profile.unsafe_ingredients.add(ingredient)

        profile.save()

        return Response({
            'success': True,
            'ingredient': ingredient.inci_name,
            'color': color,
            'message': f'{ingredient.inci_name} set to {color}'
        })

    @action(detail=False, methods=['post'])
    def set_multiple_colors(self, request):
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)

        ingredients_data = request.data.get('ingredients', [])

        if not ingredients_data:
            return Response({
                'error': 'No ingredients provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []
        errors = []

        for item in ingredients_data:
            serializer = UpdatePreferencesSerializer(data=item)
            if not serializer.is_valid():
                errors.append({
                    'data': item,
                    'error': serializer.errors
                })
                continue

            ingredient_id = serializer.validated_data['ingredient_id']
            color = serializer.validated_data['color']

            try:
                ingredient = Ingredient.objects.get(id=ingredient_id)

                profile.safe_ingredients.remove(ingredient)
                profile.moderate_ingredients.remove(ingredient)
                profile.unsafe_ingredients.remove(ingredient)

                if color == 'GREEN':
                    profile.safe_ingredients.add(ingredient)
                elif color == 'YELLOW':
                    profile.moderate_ingredients.add(ingredient)
                elif color == 'RED':
                    profile.unsafe_ingredients.add(ingredient)

                results.append({
                    'ingredient': ingredient.inci_name,
                    'color': color
                })
            except Ingredient.DoesNotExist:
                errors.append({
                    'ingredient_id': ingredient_id,
                    'error': 'Ingredient not found'
                })

        profile.save()

        return Response({
            'success': len(results),
            'errors': len(errors),
            'results': results,
            'error_details': errors if errors else None
        })

    @action(detail=False, methods=['get'])
    def ingredient_color(self, request):
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response({'color': 'NONE'})

        ingredient_id = request.query_params.get('ingredient_id')

        if not ingredient_id:
            return Response({
                'error': 'Provide ingredient_id parameter'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            ingredient = Ingredient.objects.get(id=ingredient_id)
        except Ingredient.DoesNotExist:
            return Response({
                'error': 'Ingredient not found'
            }, status=status.HTTP_404_NOT_FOUND)

        if ingredient in profile.unsafe_ingredients.all():
            color = 'RED'
        elif ingredient in profile.moderate_ingredients.all():
            color = 'YELLOW'
        elif ingredient in profile.safe_ingredients.all():
            color = 'GREEN'
        else:
            color = 'NONE'

        return Response({
            'ingredient_id': ingredient.id,
            'ingredient_name': ingredient.inci_name,
            'color': color
        })

    @action(detail=False, methods=['post'])
    def toggle_favorite(self, request):
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)

        cosmetic_id = request.data.get('cosmetic_id')

        if not cosmetic_id:
            return Response({'error': 'Provide cosmetic_id'}, status=400)

        try:
            from apps.cosmetics.models import Cosmetic
            cosmetic = Cosmetic.objects.get(id=cosmetic_id)
        except Cosmetic.DoesNotExist:
            return Response({'error': 'Cosmetic not found'}, status=404)

        if cosmetic in profile.favorite_cosmetics.all():
            profile.favorite_cosmetics.remove(cosmetic)
            is_favorite = False
            message = 'Removed from favorites'
        else:
            profile.favorite_cosmetics.add(cosmetic)
            is_favorite = True
            message = 'Added to favorites'

        return Response({
            'success': True,
            'is_favorite': is_favorite,
            'message': message
        })

    @action(detail=False, methods=['get'])
    def my_favorites(self, request):
        try:
            profile = request.user.profile
            from apps.cosmetics.serializers import CosmeticSerializer
            favorites = profile.favorite_cosmetics.all()
            serializer = CosmeticSerializer(favorites, many=True)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response([])

