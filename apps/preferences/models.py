from django.db import models
from django.contrib.auth.models import User
from apps.ingredients.models import Ingredient


class UserProfile(models.Model):
    SKIN_TYPE_CHOICES = [
        ('DRY', 'Dry'),
        ('OILY', 'Oily'),
        ('COMBINATION', 'Combination'),
        ('SENSITIVE', 'Sensitive'),
        ('NORMAL', 'Normal'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    allergic_to = models.ManyToManyField(
        Ingredient,
        blank=True,
        related_name='allergic_users',
        verbose_name="Allergic to ingredients"
    )

    avoided_ingredients = models.ManyToManyField(
        Ingredient,
        blank=True,
        related_name='avoided_by_users',
        verbose_name="Avoided ingredients (not allergic, but prefer to avoid)"
    )

    preferred_ingredients = models.ManyToManyField(
        Ingredient,
        blank=True,
        related_name='preferred_by_users',
        verbose_name="Preferred ingredients"
    )

    skin_type = models.CharField(
        max_length=20,
        choices=SKIN_TYPE_CHOICES,
        blank=True,
        verbose_name="Skin type"
    )

    skin_concerns = models.TextField(
        blank=True,
        verbose_name="Skin concerns",
        help_text="Acne, wrinkles, dark spots, redness..."
    )

    vegan_only = models.BooleanField(
        default=False,
        verbose_name="Vegan products only"
    )

    cruelty_free_only = models.BooleanField(
        default=False,
        verbose_name="Cruelty-free products only"
    )

    fragrance_free = models.BooleanField(
        default=False,
        verbose_name="Fragrance-free products preferred"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_all_unwanted_ingredients(self):
        allergies = set(self.allergic_to.all())
        avoided = set(self.avoided_ingredients.all())
        return allergies.union(avoided)

    def is_cosmetic_safe(self, cosmetic):
        unwanted = self.get_all_unwanted_ingredients()
        cosmetic_ingredients = set(cosmetic.ingredients.all())
        dangerous = unwanted.intersection(cosmetic_ingredients)
        return len(dangerous) == 0, list(dangerous)
