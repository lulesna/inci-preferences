from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.response import Response
from .models import Ingredient, IngredientEditProposal
from .serializers import IngredientSerializer


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
