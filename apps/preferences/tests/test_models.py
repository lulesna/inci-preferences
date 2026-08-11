from django.test import TestCase
from django.contrib.auth.models import User

from apps.cosmetics.models import Cosmetic
from apps.ingredients.models import Ingredient
from apps.preferences.models import UserProfile


class UserProfileTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass12345')
        self.profile = UserProfile.objects.create(user=self.user)

        self.aqua = Ingredient.objects.create(inci_name="Aqua", purpose="Solvent")
        self.fragrance = Ingredient.objects.create(inci_name="Fragrance", purpose="Perfuming")
        self.parabens = Ingredient.objects.create(inci_name="Parabens", purpose="Preservative")

        self.profile.safe_ingredients.add(self.aqua)
        self.profile.moderate_ingredients.add(self.fragrance)
        self.profile.unsafe_ingredients.add(self.parabens)

    def make_cosmetic(self, name, ingredients_text):
        cosmetic = Cosmetic.objects.create(
            name=name,
            brand="Marka",
            main_category="FACE",
            ingredients_text=ingredients_text,
        )
        cosmetic.parse_and_add_ingredients(auto_create=False)
        return cosmetic

    def test_str_returns_username(self):
        self.assertEqual(str(self.profile), "testuser's profile")

    def test_safety_details_group_ingredients_by_color(self):
        cosmetic = self.make_cosmetic("Mieszany", "Aqua, Fragrance, Parabens")

        details = self.profile.get_cosmetic_safety_details(cosmetic)

        self.assertEqual(details['color'], 'RED')
        self.assertEqual(details['safe_ingredients'], ['Aqua'])
        self.assertEqual(details['moderate_ingredients'], ['Fragrance'])
        self.assertEqual(details['unsafe_ingredients'], ['Parabens'])

    def test_unclassified_ingredients_count_as_safe(self):
        Ingredient.objects.create(inci_name="Glycerin", purpose="Humectant")
        cosmetic = self.make_cosmetic("Neutralny", "Glycerin")

        details = self.profile.get_cosmetic_safety_details(cosmetic)

        self.assertEqual(details['color'], 'GREEN')
        self.assertEqual(details['safe_ingredients'], [])
        self.assertEqual(details['moderate_ingredients'], [])
        self.assertEqual(details['unsafe_ingredients'], [])

    def test_unsafe_wins_over_moderate(self):
        cosmetic = self.make_cosmetic("Dwa ostrzezenia", "Fragrance, Parabens")

        self.assertEqual(self.profile.get_cosmetic_safety_color(cosmetic), 'RED')

    def test_ingredient_set_is_cached_per_instance(self):
        # po zmianie preferencji trzeba pobrać profil na nowo
        self.assertEqual(self.profile._safe_ingredient_set, {self.aqua})

        self.profile.safe_ingredients.add(self.fragrance)

        self.assertEqual(self.profile._safe_ingredient_set, {self.aqua})

        reloaded = UserProfile.objects.get(pk=self.profile.pk)
        self.assertEqual(reloaded._safe_ingredient_set, {self.aqua, self.fragrance})
