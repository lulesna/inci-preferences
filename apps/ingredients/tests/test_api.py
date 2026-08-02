from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from apps.ingredients.models import Ingredient


class IngredientAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.ingredient1 = Ingredient.objects.create(inci_name="Aqua", purpose="Solvent")
        self.ingredient2 = Ingredient.objects.create(inci_name="Glycerin", purpose="Humectant")
        self.ingredient3 = Ingredient.objects.create(inci_name="Niacinamide", purpose="Skin conditioning")

    def test_list_ingredients_public(self):
        response = self.client.get('/api/ingredients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_get_ingredient_detail(self):
        response = self.client.get(f'/api/ingredients/{self.ingredient1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['inci_name'], "Aqua")
        self.assertEqual(response.data['purpose'], "Solvent")

    def test_search_ingredient_by_name(self):
        response = self.client.get('/api/ingredients/?search=Niacin')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ingredient_names = [ing['inci_name'] for ing in response.data]
        self.assertIn('Niacinamide', ingredient_names)

    def test_search_ingredient_case_insensitive(self):
        response = self.client.get('/api/ingredients/?search=aqua')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_search_nonexistent_ingredient(self):
        response = self.client.get('/api/ingredients/?search=XYZNonExistent')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_ingredient_requires_authentication(self):
        response = self.client.post('/api/ingredients/', {
            'inci_name': 'New Ingredient',
            'purpose': 'Testing'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_ingredient_authenticated(self):
        user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=user)

        response = self.client.post('/api/ingredients/', {
            'inci_name': 'Hyaluronic Acid',
            'purpose': 'Hydration'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Ingredient.objects.filter(inci_name='Hyaluronic Acid').exists())