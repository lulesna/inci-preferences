from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.cosmetics.models import Cosmetic, CosmeticEditProposal
from apps.ingredients.models import Ingredient


class CosmeticAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=self.user)

        self.aqua = Ingredient.objects.create(inci_name="Aqua", purpose="Solvent")
        self.glycerin = Ingredient.objects.create(inci_name="Glycerin", purpose="Humectant")

        self.cosmetic = Cosmetic.objects.create(
            name="Test Cream",
            brand="Test Brand",
            main_category="FACE",
            subcategory="MOISTURIZER",
            ingredients_text="Aqua, Glycerin"
        )
        self.cosmetic.parse_and_add_ingredients(auto_create=False)

    def test_list_cosmetics_public(self):
        """test że niezalogowany user może pobrać listę"""
        self.client.force_authenticate(user=None)  # wyloguj
        response = self.client.get('/api/cosmetics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_list_cosmetics_authenticated(self):
        """test że zalogowany user może pobrać listę"""
        response = self.client.get('/api/cosmetics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_get_cosmetic_detail(self):
        response = self.client.get(f'/api/cosmetics/{self.cosmetic.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Test Cream")
        self.assertEqual(response.data['brand'], "Test Brand")

    def test_search_cosmetic_by_name(self):
        response = self.client.get('/api/cosmetics/?search=Test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_filter_by_main_category(self):
        response = self.client.get('/api/cosmetics/?main_category=FACE')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for cosmetic in response.data['results']:
            self.assertEqual(cosmetic['main_category'], 'FACE')

    def test_create_cosmetic_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.post('/api/cosmetics/', {
            'name': 'New Cosmetic',
            'brand': 'New Brand',
            'main_category': 'FACE',
            'ingredients_text': 'Aqua, Glycerin'
        }, format='json')
        # w zależności od uprawnień może być 401 lub 403
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_create_cosmetic_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/cosmetics/', {
            'name': 'New Cosmetic',
            'brand': 'New Brand',
            'main_category': 'FACE',
            'subcategory': 'MOISTURIZER',
            'ingredients_text': 'Aqua, Glycerin'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Cosmetic.objects.filter(name='New Cosmetic').exists())

    def test_ingredients_included_in_response(self):
        """test że składniki są zwracane w response"""
        response = self.client.get(f'/api/cosmetics/{self.cosmetic.id}/')
        self.assertIn('ingredients', response.data)
        self.assertEqual(len(response.data['ingredients']), 2)

    def test_update_by_regular_user_creates_pending_proposal(self):
        """edycja przez zwykłego usera nie zmienia obiektu od razu, tylko trafia do kolejki"""
        response = self.client.patch(f'/api/cosmetics/{self.cosmetic.id}/', {
            'name': 'Renamed Cream'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        self.cosmetic.refresh_from_db()
        self.assertEqual(self.cosmetic.name, 'Test Cream')

        proposal = CosmeticEditProposal.objects.get(cosmetic=self.cosmetic)
        self.assertEqual(proposal.status, 'PENDING')
        self.assertEqual(proposal.proposed_data['name'], 'Renamed Cream')
        self.assertEqual(proposal.submitted_by, self.user)

    def test_delete_requires_admin(self):
        response = self.client.delete(f'/api/cosmetics/{self.cosmetic.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Cosmetic.objects.filter(id=self.cosmetic.id).exists())

    def test_delete_by_admin_succeeds(self):
        admin_user = User.objects.create_superuser(username='admin', password='adminpass123')
        self.client.force_authenticate(user=admin_user)

        response = self.client.delete(f'/api/cosmetics/{self.cosmetic.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Cosmetic.objects.filter(id=self.cosmetic.id).exists())

    def test_approving_proposal_applies_change(self):
        proposal = CosmeticEditProposal.objects.create(
            cosmetic=self.cosmetic,
            proposed_data={'name': 'Approved Name'},
            submitted_by=self.user,
        )

        admin_user = User.objects.create_superuser(username='admin2', password='adminpass123')
        proposal.approve(reviewer=admin_user)

        self.cosmetic.refresh_from_db()
        self.assertEqual(self.cosmetic.name, 'Approved Name')
        self.assertEqual(proposal.status, 'APPROVED')
        self.assertEqual(proposal.reviewed_by, admin_user)

    def test_approving_ingredients_change_reparses_ingredient_list(self):
        """zatwierdzenie nowego składu musi przebudować powiązania"""
        proposal = CosmeticEditProposal.objects.create(
            cosmetic=self.cosmetic,
            proposed_data={'ingredients_text': 'Aqua, Panthenol'},
            submitted_by=self.user,
        )

        admin_user = User.objects.create_superuser(username='admin3', password='adminpass123')
        proposal.approve(reviewer=admin_user)

        self.cosmetic.refresh_from_db()
        names = set(self.cosmetic.ingredients.values_list('inci_name', flat=True))

        self.assertEqual(self.cosmetic.ingredients_text, 'Aqua, Panthenol')
        self.assertIn('Panthenol', names)


class IngredientAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        Ingredient.objects.create(inci_name="Aqua", purpose="Solvent")
        Ingredient.objects.create(inci_name="Glycerin", purpose="Humectant")
        Ingredient.objects.create(inci_name="Niacinamide", purpose="Skin conditioning")

    def test_list_ingredients(self):
        response = self.client.get('/api/ingredients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_search_ingredient(self):
        response = self.client.get('/api/ingredients/?search=Niacin')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
        ingredient_names = [ing['inci_name'] for ing in response.data['results']]
        self.assertIn('Niacinamide', ingredient_names)
