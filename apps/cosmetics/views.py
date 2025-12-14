from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Cosmetic
from .serializers import CosmeticSerializer


class CosmeticViewSet(viewsets.ModelViewSet):
    queryset = Cosmetic.objects.all()
    serializer_class = CosmeticSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['main_category', 'subcategory', 'brand']
    search_fields = ['name', 'brand']