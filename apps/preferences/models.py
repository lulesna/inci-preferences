from django.db import models
from django.contrib.auth.models import User
from apps import cosmetics
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

    def get_cosmetic_safety_color(self, cosmetic):
        cosmetic_ingredients = set(cosmetic.ingredients.all())

        unsafe = set(self.unsafe_ingredients.all())
        if cosmetic_ingredients.intersection(unsafe):
            return 'RED'

        moderate = set(self.moderate_ingredients.all())
        if cosmetic_ingredients.intersection(moderate):
            return 'YELLOW'

        return 'GREEN'

    def get_cosmetic_safety_details(self, cosmetic):
        cosmetic_ingredients = set(cosmetic.ingredients.all())

        unsafe = set(self.unsafe_ingredients.all()).intersection(cosmetic_ingredients)
        moderate = set(self.moderate_ingredients.all()).intersection(cosmetic_ingredients)
        safe = set(self.safe_ingredients.all()).intersection(cosmetic_ingredients)

        color = self.get_cosmetic_safety_color(cosmetic)

        return {
            'color': color,
            'safe_ingredients': [ing.inci_name for ing in safe],
            'moderate_ingredients': [ing.inci_name for ing in moderate],
            'unsafe_ingredients': [ing.inci_name for ing in unsafe],
        }