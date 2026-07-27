from django.test import TestCase
from apps.cosmetics.models import Cosmetic
from apps.ingredients.models import Ingredient


class CosmeticModelTest(TestCase):
    def setUp(self):
        self.ingredient = Ingredient.objects.create(
            inci_name="Aqua",
            purpose="Solvent"
        )
        self.cosmetic = Cosmetic.objects.create(
            name="Test Cream",
            brand="Test Brand",
            main_category="FACE",
            subcategory="MOISTURIZER",
            ingredients_text="Aqua, Glycerin"
        )

    def test_cosmetic_creation(self):
        self.assertEqual(self.cosmetic.name, "Test Cream")
        self.assertEqual(str(self.cosmetic), "Test Cream - Test Brand")

    def test_parse_ingredients(self):
        result = self.cosmetic.parse_and_add_ingredients(auto_create=True)
        self.assertIn("Aqua", result['matched'])
        self.assertEqual(self.cosmetic.ingredients.count(), 2)