from django.db import models
from apps.ingredients.models import Ingredient

class Cosmetic(models.Model):
    CATEGORIES = [
        ('FACE', 'Twarz'),
        ('BODY', 'Ciało'),
        ('HAIR', 'Włosy'),
        ('MAKEUP', 'Makijaż'),
        ('HANDS', 'Dłonie'),
    ]

    name = models.CharField(max_length=100, verbose_name="Nazwa")
    brand = models.CharField(max_length=100, verbose_name="Marka")
    category = models.CharField(max_length=100, choices=CATEGORIES, verbose_name="Kategoria")
    ingredients = models.ManyToManyField(Ingredient, related_name='cosmetics', verbose_name="Składniki")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kosmetyk"
        verbose_name_plural = "Kosmetyki"

    def __str__(self):
        return f"{self.name} - {self.brand}"
