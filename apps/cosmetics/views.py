from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Cosmetic
from .serializers import CosmeticSerializer
from ..ingredients.models import Ingredient


def _get_safety_message(is_safe, has_unwanted, allergy_count):
    if not is_safe:
        return f"This product contains {allergy_count} ingredient(s) you're allergic to."
    elif has_unwanted:
        return "This product contains ingredients you prefer to avoid."
    else:
        return "This product is safe for you."


class CosmeticViewSet(viewsets.ModelViewSet):
    queryset = Cosmetic.objects.all()
    serializer_class = CosmeticSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['main_category', 'subcategory', 'brand']
    search_fields = ['name', 'brand']

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def check_safety(self, request, pk=None):
        cosmetic = self.get_object()

        try:
            profile = request.user.profile
        except:
            return Response({
                'error': 'User not found.'
            }, status=400)

        user_allergies = set(profile.allergic_to.all())
        user_avoided = set(profile.avoided_ingredients.all())
        cosmetic_ingredients = set(cosmetic.ingredients.all())

        dangerous_allergies = user_allergies.intersection(cosmetic_ingredients)
        unwanted = user_avoided.intersection(cosmetic_ingredients)

        is_safe = len(dangerous_allergies) == 0
        has_unwanted = len(unwanted) > 0

        return Response({
            'cosmetic_name': cosmetic.name,
            'brand': cosmetic.brand,
            'is_safe': is_safe,
            'has_unwanted_ingredients': has_unwanted,
            'dangerous_ingredients': [
                {
                    'id': ingredient.id,
                    'inci_name': ingredient.inci_name,
                    'purpose': ingredient.purpose
                }
                for ingredient in dangerous_allergies
            ],
            'unwanted_ingredients': [
                {
                    'id': ing.id,
                    'inci_name': ing.inci_name,
                    'purpose': ing.purpose
                }
                for ing in unwanted
            ],
            'total_ingredients': cosmetic_ingredients.__len__(),
            'message': _get_safety_message(is_safe, has_unwanted, len(dangerous_allergies))
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def analyze_all(self, request):
        try:
            profile = request.user.profile
        except:
            return Response({
                'error': 'User profile not found.'
            }, status=400)

        user_unwanted = profile.get_all_unwanted_ingredients()

        results = {
            'safe': [],
            'unsafe': [],
            'with_unwanted': []
        }

        for cosmetic in self.queryset.all():
            cosmetic_ingredients = set(cosmetic.ingredients.all())
            dangerous = user_unwanted.intersection(cosmetic_ingredients)

            cosmetic_data = {
                'id': cosmetic.id,
                'name': cosmetic.name,
                'brand': cosmetic.brand,
                'category': cosmetic.main_category
            }

            if len(dangerous) == 0:
                results['safe'].append(cosmetic_data)
            else:
                results['unsafe'].append({
                    **cosmetic_data,
                    'dangerous_count': len(dangerous)
                })

        return Response({
            'total_cosmetics': self.queryset.count(),
            'safe_count': len(results['safe']),
            'unsafe_count': len(results['unsafe']),
            'results': results,
            'user': request.user.username
        })

    @action(detail=False, methods=['get'])
    def by_ingredient(self, request):
        ingredient_name = request.query_params.get('ingredient', '')

        if not ingredient_name:
            return Response({'error': 'Provide ingredient parameter'}, status=400)

        try:
            ingredient = Ingredient.objects.get(inci_name__iexact=ingredient_name)
            cosmetics = self.queryset.filter(ingredients=ingredient)
            serializer = self.get_serializer(cosmetics, many=True)

            return Response({
                'ingredient': ingredient.inci_name,
                'count': cosmetics.count(),
                'cosmetics': serializer.data
            })
        except Ingredient.DoesNotExist:
            return Response({'error': 'Ingredient not found'}, status=404)
