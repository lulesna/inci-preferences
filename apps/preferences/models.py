from django.db import models
from django.contrib.auth.models import User
from django.utils.functional import cached_property
from apps.ingredients.models import Ingredient


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    safe_ingredients = models.ManyToManyField(
        Ingredient,
        blank=True,
        related_name='safe_for_users',
        verbose_name="Safe ingredients (GREEN)"
    )

    moderate_ingredients = models.ManyToManyField(
        Ingredient,
        blank=True,
        related_name='moderate_for_users',
        verbose_name="Moderate ingredients (YELLOW)"
    )

    unsafe_ingredients = models.ManyToManyField(
        Ingredient,
        blank=True,
        related_name='unsafe_for_users',
        verbose_name="Unsafe ingredients (RED)"
    )

    favorite_cosmetics = models.ManyToManyField(
        'cosmetics.Cosmetic',
        blank=True,
        related_name='favorited_by',
        verbose_name="Favorite Cosmetics"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username}'s profile"

    # Cache'owane per-instancja profilu, żeby przy serializacji listy kosmetyków
    # (kolor bezpieczeństwa liczony osobno dla każdego produktu) nie odpytywać
    # tych samych M2M-ów od nowa za każdym razem.
    @cached_property
    def _unsafe_ingredient_set(self):
        return set(self.unsafe_ingredients.all())

    @cached_property
    def _moderate_ingredient_set(self):
        return set(self.moderate_ingredients.all())

    @cached_property
    def _safe_ingredient_set(self):
        return set(self.safe_ingredients.all())

    def get_cosmetic_safety_color(self, cosmetic):
        cosmetic_ingredients = set(cosmetic.ingredients.all())

        if cosmetic_ingredients.intersection(self._unsafe_ingredient_set):
            return 'RED'

        if cosmetic_ingredients.intersection(self._moderate_ingredient_set):
            return 'YELLOW'

        return 'GREEN'

    def get_cosmetic_safety_details(self, cosmetic):
        cosmetic_ingredients = set(cosmetic.ingredients.all())

        unsafe = self._unsafe_ingredient_set.intersection(cosmetic_ingredients)
        moderate = self._moderate_ingredient_set.intersection(cosmetic_ingredients)
        safe = self._safe_ingredient_set.intersection(cosmetic_ingredients)

        color = self.get_cosmetic_safety_color(cosmetic)

        return {
            'color': color,
            'safe_ingredients': [ing.inci_name for ing in safe],
            'moderate_ingredients': [ing.inci_name for ing in moderate],
            'unsafe_ingredients': [ing.inci_name for ing in unsafe],
        }