from django.db.models.functions import Length, Lower
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.response import Response
from .models import Ingredient, IngredientEditProposal
from .serializers import IngredientSerializer

# tyle nazw wystarczy na najdłuższy skład, jaki da się odczytać ze zdjęcia
LOOKUP_LIMIT = 200


def _distance(first, second):
    """Levenshtein, bez zewnętrznej biblioteki dla jednej funkcji"""
    if first == second:
        return 0

    previous = list(range(len(second) + 1))
    for i, left in enumerate(first, 1):
        current = [i]
        for j, right in enumerate(second, 1):
            current.append(min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (left != right),
            ))
        previous = current

    return previous[-1]


# Progi dobrane na literówkach, które OCR zrobił na prawdziwych etykietach
# ('parkn butter', 'glycerwl stearate', 'arfum'), i sprawdzone na parach, których
# pomylić nie wolno: 'citric acid' i 'lactic acid' dzieli dystans 4, a
# 'glyceryl stearate' od 'glyceryl stearate se' - 3, więc oba zostają osobne.
def _is_close(query, candidate):
    if len(query.split()) != len(candidate.split()):
        return False

    limit = 1 if max(len(query), len(candidate)) < 12 else 2
    return _distance(query, candidate) <= limit


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]  # GET publiczne, POST dla zalogowanych
    filter_backends = [filters.SearchFilter]
    search_fields = ['inci_name']

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdminUser()]
        return super().get_permissions()

    # skaner ma po OCR same nazwy, a do oceny składnika i pokazania jego
    # zastosowania potrzebne jest id z katalogu. jedno zapytanie zamiast
    # osobnego wyszukiwania dla każdej z kilkudziesięciu pozycji
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def lookup(self, request):
        names = request.data.get('names')

        if not isinstance(names, list):
            return Response(
                {'names': ['Expected a list of INCI names.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        queries = []
        seen = set()
        for name in names[:LOOKUP_LIMIT]:
            cleaned = ' '.join(str(name).split()).lower()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                queries.append(cleaned)

        if not queries:
            return Response([])

        # __in jest w Postgresie wrażliwe na wielkość liter, a ze zdjęcia
        # przychodzi 'AQUA' albo 'aqua' zamiast katalogowego 'Aqua'
        catalogue = Ingredient.objects.annotate(name_lower=Lower('inci_name'))
        exact = {item.name_lower: item for item in catalogue.filter(name_lower__in=queries)}

        results = []
        pending = [query for query in queries if query not in exact]

        # kandydaci do dopasowania przybliżonego: tylko zbliżonej długości,
        # żeby nie liczyć dystansu całego katalogu do każdej odczytanej nazwy
        candidates = []
        if pending:
            shortest = min(len(query) for query in pending) - 2
            longest = max(len(query) for query in pending) + 2
            candidates = list(
                catalogue.annotate(name_length=Length('inci_name'))
                .filter(name_length__gte=max(shortest, 1), name_length__lte=longest)
            )

        for query in queries:
            found = exact.get(query)
            kind = 'exact'

            if not found:
                close = [item for item in candidates if _is_close(query, item.name_lower)]
                if close:
                    # najbliższy dystansem, przy remisie krótszy
                    close.sort(key=lambda item: (_distance(query, item.name_lower), len(item.inci_name)))
                    found = close[0]
                    kind = 'fuzzy'

            if found:
                results.append({
                    'query': query,
                    'match': kind,
                    'ingredient': IngredientSerializer(found).data,
                })

        return Response(results)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.get('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        IngredientEditProposal.objects.create(
            ingredient=instance,
            proposed_data=dict(serializer.validated_data),
            submitted_by=request.user,
        )

        return Response(
            {'detail': 'Change submitted for admin review.'},
            status=status.HTTP_202_ACCEPTED
        )
