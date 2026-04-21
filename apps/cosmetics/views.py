from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Cosmetic
from .serializers import CosmeticSerializer, CosmeticWithSafetySerializer
from apps.ingredients.models import Ingredient
from apps.preferences.models import UserProfile


class CosmeticViewSet(viewsets.ModelViewSet):
    queryset = Cosmetic.objects.all()
    serializer_class = CosmeticSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['main_category', 'subcategory', 'brand']
    search_fields = ['name', 'brand']

    def perform_create(self, serializer):
        cosmetic = serializer.save()

        if 'ingredients_text' in self.request.data and self.request.data['ingredients_text']:
            cosmetic.ingredients_text = self.request.data['ingredients_text']
            cosmetic.save()
            cosmetic.parse_and_add_ingredients(auto_create=True)

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

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def recommended(self, request):
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response({'error': 'No profile found'}, status=400)

        safe_ingredients = set(profile.safe_ingredients.all())
        moderate_ingredients = set(profile.moderate_ingredients.all())
        unsafe_ingredients = set(profile.unsafe_ingredients.all())

        recommendations = []

        for cosmetic in self.queryset.all():
            cosmetic_ingredients = set(cosmetic.ingredients.all())

            has_moderate = bool(cosmetic_ingredients.intersection(moderate_ingredients))
            has_unsafe = bool(cosmetic_ingredients.intersection(unsafe_ingredients))

            if has_moderate or has_unsafe:
                continue

            safe_count = len(cosmetic_ingredients.intersection(safe_ingredients))

            if safe_count > 0:
                recommendations.append({
                    'cosmetic': cosmetic,
                    'safe_count': safe_count
                })

        recommendations.sort(key=lambda x: x['safe_count'], reverse=True)

        top_recommendations = recommendations[:10]

        from apps.cosmetics.serializers import CosmeticSerializer
        serialized = [
            {
                **CosmeticSerializer(rec['cosmetic']).data,
                'safe_ingredients_count': rec['safe_count']
            }
            for rec in top_recommendations
        ]

        return Response({
            'count': len(serialized),
            'recommendations': serialized
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

    @action(detail=True, methods=['get'])
    def find_dupes(self, request, pk=None):
        original = self.get_object()
        original_ingredients = set(ing.id for ing in original.ingredients.all())

        if len(original_ingredients) == 0:
            return Response({'error': 'This cosmetic has no ingredients'}, status=400)

        dupes = []

        candidates = self.queryset.filter(
            main_category=original.main_category
        ).exclude(id=original.id)

        for cosmetic in candidates:
            cosmetic_ingredients = set(ing.id for ing in cosmetic.ingredients.all())

            if len(cosmetic_ingredients) == 0:
                continue

            matching = len(original_ingredients & cosmetic_ingredients)

            similarity = (matching / len(original_ingredients)) * 100

            # min 50% składników się pokrywa
            if similarity >= 50:
                dupes.append({
                    'cosmetic': cosmetic,
                    'similarity': round(similarity, 1),
                    'matching': matching
                })

        dupes.sort(key=lambda x: x['similarity'], reverse=True)

        # top 10
        from apps.cosmetics.serializers import CosmeticSerializer
        result = [
            {
                **CosmeticSerializer(d['cosmetic']).data,
                'similarity_score': d['similarity'],
                'matching_ingredients_count': d['matching']
            }
            for d in dupes[:10]
        ]

        return Response({
            'original': CosmeticSerializer(original).data,
            'dupes': result
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def analyze_favorites(self, request):
        try:
            profile = request.user.profile
        except:
            return Response({'error': 'No profile found'}, status=400)

        favorites = profile.favorite_cosmetics.all()

        if favorites.count() < 3:
            return Response({
                'message': 'Add at least 3 favorites to get ingredient insights',
                'suggestions': []
            })

        ingredient_counts = {}
        total_favorites = favorites.count()

        for cosmetic in favorites:
            for ingredient in cosmetic.ingredients.all():
                # pominięcie składników już oznaczone przez użytkownika
                if (ingredient.id in profile.safe_ingredients.all().values_list('id', flat=True) or
                        ingredient.id in profile.moderate_ingredients.all().values_list('id', flat=True) or
                        ingredient.id in profile.unsafe_ingredients.all().values_list('id', flat=True)):
                    continue

                if ingredient.id not in ingredient_counts:
                    ingredient_counts[ingredient.id] = {
                        'ingredient': ingredient,
                        'count': 0
                    }
                ingredient_counts[ingredient.id]['count'] += 1

        # sortowanie po częstotliwości
        sorted_ingredients = sorted(
            ingredient_counts.values(),
            key=lambda x: x['count'],
            reverse=True
        )

        # top 5 składników które występują w min 50% ulubionych
        suggestions = []
        for item in sorted_ingredients[:10]:
            percentage = (item['count'] / total_favorites) * 100
            if percentage >= 50:
                suggestions.append({
                    'ingredient_id': item['ingredient'].id,
                    'ingredient_name': item['ingredient'].inci_name,
                    'count': item['count'],
                    'percentage': round(percentage, 1),
                    'total_favorites': total_favorites
                })

        return Response({
            'total_favorites': total_favorites,
            'suggestions': suggestions[:5]  # max 5 sugestii
        })
