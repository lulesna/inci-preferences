from django.db import models

class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nazwa")
    inci_name = models.CharField(max_length=200, verbose_name="Nazwa INCI")
    description = models.TextField(blank=True, verbose_name="Opis")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Składnik"
        verbose_name_plural = "Składniki"

    def __str__(self):
        return self.name
