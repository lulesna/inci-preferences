from django.test import TestCase
from django.db import IntegrityError
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

    def test_ingredient_unique_inci_name(self):
        with self.assertRaises(IntegrityError):
            Ingredient.objects.create(
                inci_name="Aqua",
                purpose="Different purpose"
            )

    def test_ingredient_without_purpose(self):
        ingredient = Ingredient.objects.create(inci_name="Glycerin")
        self.assertEqual(ingredient.inci_name, "Glycerin")

    def test_ingredient_created_at_auto_set(self):
        self.assertIsNotNone(self.ingredient.created_at)

    def test_multiple_ingredients_creation(self):
        Ingredient.objects.create(inci_name="Glycerin", purpose="Humectant")
        Ingredient.objects.create(inci_name="Niacinamide", purpose="Skin conditioning")

        self.assertEqual(Ingredient.objects.count(), 3)

    def test_ingredient_query_by_name(self):
        found = Ingredient.objects.get(inci_name="Aqua")
        self.assertEqual(found.id, self.ingredient.id)

    def test_ingredient_case_sensitive_search(self):
        Ingredient.objects.create(inci_name="Niacinamide", purpose="Vitamin B3")

        results = Ingredient.objects.filter(inci_name__icontains="niacin")
        self.assertEqual(results.count(), 1)
