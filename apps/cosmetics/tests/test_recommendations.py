from django.test import TestCase
from django.contrib.auth.models import User
from apps.cosmetics.models import Cosmetic
from apps.ingredients.models import Ingredient
from apps.preferences.models import UserProfile


class SafetyAnalysisTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)

        self.safe_ing = Ingredient.objects.create(inci_name="Aqua")
        self.moderate_ing = Ingredient.objects.create(inci_name="Fragrance")
        self.unsafe_ing = Ingredient.objects.create(inci_name="Parabens")

        self.profile.safe_ingredients.add(self.safe_ing)
        self.profile.moderate_ingredients.add(self.moderate_ing)
        self.profile.unsafe_ingredients.add(self.unsafe_ing)

    def test_cosmetic_with_only_safe_ingredients(self):
        cosmetic = Cosmetic.objects.create(
            name="Safe Product",
            brand="Brand",
            main_category="FACE",
            ingredients_text="Aqua"
        )
        cosmetic.parse_and_add_ingredients(auto_create=False)

        color = self.profile.get_cosmetic_safety_color(cosmetic)
        self.assertEqual(color, 'GREEN')

    def test_cosmetic_with_moderate_ingredients(self):
        cosmetic = Cosmetic.objects.create(
            name="Moderate Product",
            brand="Brand",
            main_category="FACE",
            ingredients_text="Aqua, Fragrance"
        )
        cosmetic.parse_and_add_ingredients(auto_create=False)

        color = self.profile.get_cosmetic_safety_color(cosmetic)
        self.assertEqual(color, 'YELLOW')

    def test_cosmetic_with_unsafe_ingredients(self):
        cosmetic = Cosmetic.objects.create(
            name="Unsafe Product",
            brand="Brand",
            main_category="FACE",
            ingredients_text="Aqua, Parabens"
        )
        cosmetic.parse_and_add_ingredients(auto_create=False)

        color = self.profile.get_cosmetic_safety_color(cosmetic)
        self.assertEqual(color, 'RED')

    def test_favorites_functionality(self):
        cosmetic = Cosmetic.objects.create(
            name="Fav Product",
            brand="Brand",
            main_category="FACE"
        )

        self.profile.favorite_cosmetics.add(cosmetic)
        self.assertTrue(self.profile.favorite_cosmetics.filter(id=cosmetic.id).exists())

        self.profile.favorite_cosmetics.remove(cosmetic)
        self.assertFalse(self.profile.favorite_cosmetics.filter(id=cosmetic.id).exists())