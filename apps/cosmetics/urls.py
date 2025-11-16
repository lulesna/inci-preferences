from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CosmeticViewSet

router = DefaultRouter()
router.register(r'cosmetics', CosmeticViewSet)

urlpatterns = [
    path('', include(router.urls)),
]