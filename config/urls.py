from django.contrib import admin
from django.urls import path, include
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('apps.users.urls')),
    path('', views.index, name='index'),
    path('profile/', views.profile, name='profile'),
    path('favorites/', views.favorites, name='favorites'),
    path('categories/', views.categories, name='categories'),
    path('categories/skincare', views.skincare, name='skincare'),
    path('categories/makeup', views.makeup, name='makeup'),
    path('categories/bodycare', views.bodycare, name='bodycare'),
    path('search/', views.search, name='search'),
    path('cosmetic/<int:pk>/', views.cosmetic_detail, name='cosmetic_detail'),
    path('dupes/', TemplateView.as_view(template_name='dupes.html'), name='dupes'),
    path('scan/', TemplateView.as_view(template_name='scan.html'), name='scan'),

    path('categories/makeup/makeup_eyes', views.makeup_eyes, name='makeup_eyes'),
    path('categories/makeup/makeup_face', views.makeup_face, name='makeup_face'),
    path('categories/makeup/makeup_lips', views.makeup_lips, name='makeup_lips'),

    path('categories/skincare/skincare_cleanser', views.skincare_cleanser, name='skincare_cleanser'),
    path('categories/skincare/skincare_moisturizer', views.skincare_moisturizer, name='skincare_moisturizer'),
    path('categories/skincare/skincare_serum', views.skincare_serum, name='skincare_serum'),
    path('categories/skincare/skincare_sunscreen', views.skincare_sunscreen, name='skincare_sunscreen'),
    path('categories/skincare/skincare_toner', views.skincare_toner, name='skincare_toner'),

    path('addcosmetic/', views.add_cosmetic, name='addcosmetic'),
    path('check/', views.check_cosmetic, name='check_cosmetic'),
    path('api/', include('apps.ingredients.urls')),
    path('api/', include('apps.cosmetics.urls')),
    path('api/', include('apps.preferences.urls')),
]
