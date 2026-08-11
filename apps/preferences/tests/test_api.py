from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

from apps.cosmetics.models import Cosmetic
from apps.ingredients.models import Ingredient
from apps.preferences.models import UserProfile


class PreferencesAPITest(TestCase):

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass12345')
        self.profile = UserProfile.objects.create(user=self.user)

        self.aqua = Ingredient.objects.create(inci_name="Aqua", purpose="Solvent")
        self.parabens = Ingredient.objects.create(inci_name="Parabens", purpose="Preservative")

        self.client.force_authenticate(user=self.user)

    def test_anonymous_user_has_no_access(self):
        self.client.force_authenticate(user=None)

        response = self.client.get('/api/preferences/my_preferences/')

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_my_preferences_returns_own_profile(self):
        self.profile.safe_ingredients.add(self.aqua)

        response = self.client.get('/api/preferences/my_preferences/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(
            [ing['inci_name'] for ing in response.data['safe_ingredients']],
            ['Aqua'],
        )

    def test_set_ingredient_color(self):
        response = self.client.post('/api/preferences/set_ingredient_color/', {
            'ingredient_id': self.aqua.id,
            'color': 'GREEN',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.profile.safe_ingredients.filter(id=self.aqua.id).exists())

    def test_set_ingredient_color_moves_between_groups(self):
        # składnik może należeć tylko do jednej grupy
        self.profile.safe_ingredients.add(self.aqua)

        self.client.post('/api/preferences/set_ingredient_color/', {
            'ingredient_id': self.aqua.id,
            'color': 'RED',
        })

        self.assertFalse(self.profile.safe_ingredients.filter(id=self.aqua.id).exists())
        self.assertTrue(self.profile.unsafe_ingredients.filter(id=self.aqua.id).exists())

    def test_color_none_clears_classification(self):
        self.profile.unsafe_ingredients.add(self.parabens)

        self.client.post('/api/preferences/set_ingredient_color/', {
            'ingredient_id': self.parabens.id,
            'color': 'NONE',
        })

        self.assertFalse(self.profile.safe_ingredients.filter(id=self.parabens.id).exists())
        self.assertFalse(self.profile.moderate_ingredients.filter(id=self.parabens.id).exists())
        self.assertFalse(self.profile.unsafe_ingredients.filter(id=self.parabens.id).exists())

    def test_invalid_color_rejected(self):
        response = self.client.post('/api/preferences/set_ingredient_color/', {
            'ingredient_id': self.aqua.id,
            'color': 'FIOLETOWY',
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_ingredient_returns_404(self):
        response = self.client.post('/api/preferences/set_ingredient_color/', {
            'ingredient_id': 999999,
            'color': 'GREEN',
        })

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_ingredient_color_reports_none_when_unclassified(self):
        response = self.client.get(
            '/api/preferences/ingredient_color/',
            {'ingredient_id': self.aqua.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['color'], 'NONE')

    def test_ingredient_color_reports_assigned_color(self):
        self.profile.moderate_ingredients.add(self.aqua)

        response = self.client.get(
            '/api/preferences/ingredient_color/',
            {'ingredient_id': self.aqua.id},
        )

        self.assertEqual(response.data['color'], 'YELLOW')
        self.assertEqual(response.data['ingredient_name'], 'Aqua')

    def test_ingredient_color_requires_parameter(self):
        response = self.client.get('/api/preferences/ingredient_color/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_multiple_colors_reports_successes_and_errors(self):
        response = self.client.post('/api/preferences/set_multiple_colors/', {
            'ingredients': [
                {'ingredient_id': self.aqua.id, 'color': 'GREEN'},
                {'ingredient_id': 999999, 'color': 'RED'},
            ],
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], 1)
        self.assertEqual(response.data['errors'], 1)
        self.assertTrue(self.profile.safe_ingredients.filter(id=self.aqua.id).exists())

    def test_set_multiple_colors_without_payload_rejected(self):
        response = self.client.post(
            '/api/preferences/set_multiple_colors/',
            {'ingredients': []},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_toggle_favorite_adds_then_removes(self):
        cosmetic = Cosmetic.objects.create(name="Krem", brand="Marka", main_category="FACE")

        added = self.client.post('/api/preferences/toggle_favorite/', {'cosmetic_id': cosmetic.id})

        self.assertTrue(added.data['is_favorite'])
        self.assertTrue(self.profile.favorite_cosmetics.filter(id=cosmetic.id).exists())

        removed = self.client.post('/api/preferences/toggle_favorite/', {'cosmetic_id': cosmetic.id})

        self.assertFalse(removed.data['is_favorite'])
        self.assertFalse(self.profile.favorite_cosmetics.filter(id=cosmetic.id).exists())

    def test_toggle_favorite_requires_cosmetic_id(self):
        response = self.client.post('/api/preferences/toggle_favorite/', {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_toggle_favorite_unknown_cosmetic_returns_404(self):
        response = self.client.post('/api/preferences/toggle_favorite/', {'cosmetic_id': 999999})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_my_favorites_lists_saved_cosmetics(self):
        cosmetic = Cosmetic.objects.create(name="Krem", brand="Marka", main_category="FACE")
        self.profile.favorite_cosmetics.add(cosmetic)

        response = self.client.get('/api/preferences/my_favorites/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Krem")


class PreferencesWithoutProfileTest(TestCase):
    """Konto założone poza rejestracją nie ma jeszcze wpisu UserProfile."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(username='bezprofilu', password='pass12345')
        self.aqua = Ingredient.objects.create(inci_name="Aqua", purpose="Solvent")
        self.client.force_authenticate(user=self.user)

    def test_my_preferences_returns_404(self):
        response = self.client.get('/api/preferences/my_preferences/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_setting_a_color_creates_profile(self):
        response = self.client.post('/api/preferences/set_ingredient_color/', {
            'ingredient_id': self.aqua.id,
            'color': 'GREEN',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_my_favorites_returns_empty_list(self):
        response = self.client.get('/api/preferences/my_favorites/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
