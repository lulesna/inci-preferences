from rest_framework import viewsets
from .models import Cosmetic
from .serializers import CosmeticSerializer


class CosmeticViewSet(viewsets.ModelViewSet):
    queryset = Cosmetic.objects.all()
    serializer_class = CosmeticSerializer