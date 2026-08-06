from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status
from apps.ingredients.models import Ingredient, IngredientEditProposal


class IngredientAPITest(TestCase):

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.ingredient1 = Ingredient.objects.create(inci_name="Aqua", purpose="Solvent")
        self.ingredient2 = Ingredient.objects.create(inci_name="Glycerin", purpose="Humectant")
        self.ingredient3 = Ingredient.objects.create(inci_name="Niacinamide", purpose="Skin conditioning")

    def test_list_ingredients_public(self):
        response = self.client.get('/api/ingredients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_get_ingredient_detail(self):
        response = self.client.get(f'/api/ingredients/{self.ingredient1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['inci_name'], "Aqua")
        self.assertEqual(response.data['purpose'], "Solvent")

    def test_search_ingredient_by_name(self):
        response = self.client.get('/api/ingredients/?search=Niacin')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ingredient_names = [ing['inci_name'] for ing in response.data['results']]
        self.assertIn('Niacinamide', ingredient_names)

    def test_search_ingredient_case_insensitive(self):
        response = self.client.get('/api/ingredients/?search=aqua')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_search_nonexistent_ingredient(self):
        response = self.client.get('/api/ingredients/?search=XYZNonExistent')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

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

    def test_update_by_regular_user_creates_pending_proposal(self):
        """edycja przez zwykłego usera nie zmienia obiektu od razu, tylko trafia do kolejki"""
        user = User.objects.create_user(username='testuser2', password='testpass123')
        self.client.force_authenticate(user=user)

        response = self.client.patch(f'/api/ingredients/{self.ingredient1.id}/', {
            'purpose': 'Renamed purpose'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        self.ingredient1.refresh_from_db()
        self.assertEqual(self.ingredient1.purpose, 'Solvent')

        proposal = IngredientEditProposal.objects.get(ingredient=self.ingredient1)
        self.assertEqual(proposal.status, 'PENDING')
        self.assertEqual(proposal.proposed_data['purpose'], 'Renamed purpose')

    def test_delete_requires_admin(self):
        user = User.objects.create_user(username='testuser3', password='testpass123')
        self.client.force_authenticate(user=user)

        response = self.client.delete(f'/api/ingredients/{self.ingredient1.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Ingredient.objects.filter(id=self.ingredient1.id).exists())

    def test_delete_by_admin_succeeds(self):
        admin_user = User.objects.create_superuser(username='admin', password='adminpass123')
        self.client.force_authenticate(user=admin_user)

        response = self.client.delete(f'/api/ingredients/{self.ingredient1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=self.ingredient1.id).exists())

    def test_anon_user_throttled_after_limit(self):
        """anonimowe żądania są limitowane do 100/min"""
        for _ in range(100):
            response = self.client.get('/api/ingredients/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get('/api/ingredients/')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)