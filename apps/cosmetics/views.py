from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Cosmetic
from .serializers import CosmeticSerializer, CosmeticWithSafetySerializer
from apps.ingredients.models import Ingredient


class CosmeticViewSet(viewsets.ModelViewSet):
    queryset = Cosmetic.objects.all()
    serializer_class = CosmeticSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['main_category', 'subcategory', 'brand']
    search_fields = ['name', 'brand']

    def get_serializer_class(self):
        if self.action in ['with_colors', 'list'] and self.request.user.is_authenticated:
            return CosmeticWithSafetySerializer
        return CosmeticSerializer

    @action(detail=False, methods=['get'])
    def with_colors(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)

        queryset = self.filter_queryset(self.get_queryset())
        serializer = CosmeticWithSafetySerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def check_safety(self, request, pk=None):
        cosmetic = self.get_object()

        try:
            profile = request.user.profile
        except:
            return Response({'error': 'User profile not found.'}, status=400)

        details = profile.get_cosmetic_safety_details(cosmetic)

        return Response({
            'cosmetic_id': cosmetic.id,
            'cosmetic_name': cosmetic.name,
            'brand': cosmetic.brand,
            'safety_color': details['color'],
            'safe_ingredients': details['safe_ingredients'],
            'moderate_ingredients': details['moderate_ingredients'],
            'unsafe_ingredients': details['unsafe_ingredients'],
            'message': self._get_color_message(details['color'])
        })

    def _get_color_message(self, color):
        messages = {
            'GREEN': 'Safe product! All ingredients are okay for you.',
            'YELLOW': 'Caution! Contains some moderate ingredients.',
            'RED': 'WARNING! Contains unsafe ingredients for you!'
        }
        return messages.get(color, 'Unknown')

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def by_color(self, request):
        try:
            profile = request.user.profile
        except:
            return Response({'error': 'No profile'}, status=400)

        color_filter = request.query_params.get('color', '').upper()

        if color_filter not in ['GREEN', 'YELLOW', 'RED']:
            color_filter = None

        results = {
            'green': [],
            'yellow': [],
            'red': []
        }

        for cosmetic in self.queryset.all():
            color = profile.get_cosmetic_safety_color(cosmetic)

            cosmetic_data = {
                'id': cosmetic.id,
                'name': cosmetic.name,
                'brand': cosmetic.brand,
                'category': cosmetic.main_category,
                'color': color
            }

            if color == 'GREEN':
                results['green'].append(cosmetic_data)
            elif color == 'YELLOW':
                results['yellow'].append(cosmetic_data)
            else:
                results['red'].append(cosmetic_data)

        if color_filter:
            key = color_filter.lower()
            return Response({
                'color': color_filter,
                'count': len(results[key]),
                'cosmetics': results[key]
            })

        return Response({
            'total': self.queryset.count(),
            'green_count': len(results['green']),
            'yellow_count': len(results['yellow']),
            'red_count': len(results['red']),
            'results': results
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