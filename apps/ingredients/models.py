from django.db import models

class Ingredient(models.Model):
    inci_name = models.CharField(max_length=100, unique=True, verbose_name="INCI Name")
    purpose = models.CharField(max_length=100, verbose_name="Purpose", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"
        ordering = ['id']

    def __str__(self):
        return self.inci_name
