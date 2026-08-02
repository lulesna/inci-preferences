from django.test import TestCase
from apps.cosmetics.models import Cosmetic
from apps.ingredients.models import Ingredient


class IngredientModelTest(TestCase):
    def setUp(self):
        self.ingredient = Ingredient.objects.create(
            inci_name="Aqua",
            purpose="Solvent"
        )

    def test_ingredient_creation(self):
        self.assertEqual(self.ingredient.inci_name, "Aqua")
        self.assertEqual(self.ingredient.purpose, "Solvent")

    def test_ingredient_str_representation(self):
        self.assertEqual(str(self.ingredient), "Aqua")

    def test_ingredient_unique_name(self):
        with self.assertRaises(Exception):
            Ingredient.objects.create(
                inci_name="Aqua",
                purpose="Different purpose"
            )

    def test_ingredient_without_purpose(self):
        """składnik może istnieć bez purpose"""
        ing = Ingredient.objects.create(inci_name="Glycerin")
        self.assertEqual(ing.purpose, "")


class CosmeticModelTest(TestCase):
    def setUp(self):
        self.aqua = Ingredient.objects.create(inci_name="Aqua", purpose="Solvent")
        self.glycerin = Ingredient.objects.create(inci_name="Glycerin", purpose="Humectant")
        self.niacinamide = Ingredient.objects.create(inci_name="Niacinamide", purpose="Skin conditioning")

        self.cosmetic = Cosmetic.objects.create(
            name="Test Cream",
            brand="Test Brand",
            main_category="FACE",
            subcategory="MOISTURIZER",
            ingredients_text="Aqua, Glycerin, Niacinamide"
        )

    def test_cosmetic_creation(self):
        self.assertEqual(self.cosmetic.name, "Test Cream")
        self.assertEqual(self.cosmetic.brand, "Test Brand")
        self.assertEqual(self.cosmetic.main_category, "FACE")

    def test_cosmetic_str_representation(self):
        self.assertIn("Test Cream", str(self.cosmetic))
        self.assertIn("Test Brand", str(self.cosmetic))

    def test_parse_and_add_ingredients_matches_existing(self):
        result = self.cosmetic.parse_and_add_ingredients(auto_create=False)

        self.assertEqual(len(result['matched']), 3)
        self.assertIn("Aqua", result['matched'])
        self.assertIn("Glycerin", result['matched'])
        self.assertIn("Niacinamide", result['matched'])
        self.assertEqual(self.cosmetic.ingredients.count(), 3)

    def test_parse_and_add_ingredients_creates_new(self):
        self.cosmetic.ingredients_text = "Aqua, XYZUnknownIngredient123, Glycerin"
        self.cosmetic.save()

        initial_count = Ingredient.objects.count()

        result = self.cosmetic.parse_and_add_ingredients(auto_create=True)

        self.assertEqual(Ingredient.objects.count(), initial_count + 1)
        self.assertTrue(Ingredient.objects.filter(inci_name="XYZUnknownIngredient123").exists())

    def test_parse_ingredients_case_insensitive(self):
        self.cosmetic.ingredients_text = "aqua, GLYCERIN, Niacinamide"
        self.cosmetic.save()

        result = self.cosmetic.parse_and_add_ingredients(auto_create=False)
        self.assertEqual(len(result['matched']), 3)

    def test_get_full_category(self):
        category = self.cosmetic.get_full_category()
        self.assertIsNotNone(category)

    def test_cosmetic_ingredients_relationship(self):
        self.cosmetic.parse_and_add_ingredients(auto_create=False)

        ingredient_names = list(self.cosmetic.ingredients.values_list('inci_name', flat=True))
        self.assertIn("Aqua", ingredient_names)
        self.assertEqual(self.cosmetic.ingredients.count(), 3)