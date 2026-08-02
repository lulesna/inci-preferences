from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class UserAuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='Pass123!'
        )

    def test_login_page_accessible(self):
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 200)

    def test_successful_login(self):
        login_success = self.client.login(username='testuser', password='Pass123!')
        self.assertTrue(login_success)

    def test_login_with_wrong_password(self):
        response = self.client.post(reverse('users:login'), {
            'username': 'testuser',
            'password': 'testuser1'
        })
        self.assertNotEqual(response.status_code, 302)

    def test_register_new_user(self):
        response = self.client.post(reverse('users:register'), {
            'username': 'newuser',
            'password1': 'Pass123!',
            'password2': 'Pass123!'
        })
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_password_mismatch(self):
        response = self.client.post(reverse('users:register'), {
            'username': 'newuser2',
            'password1': 'Pass123!',
            'password2': 'Pass1234!'
        })
        self.assertFalse(User.objects.filter(username='newuser2').exists())

    def test_change_password_authenticated(self):
        self.client.login(username='testuser', password='Pass123!')
        response = self.client.post(reverse('users:change_password'), {
            'old_password': 'Pass123!',
            'new_password1': 'Pass456!',
            'new_password2': 'Pass456!'
        })

        self.client.logout()
        login_success = self.client.login(username='testuser', password='Pass456!')
        self.assertTrue(login_success)

    def test_change_password_wrong_old(self):
        """nie można zmienić hasła bez znajomości starego"""
        self.client.login(username='testuser', password='Pass123!')
        response = self.client.post(reverse('users:change_password'), {
            'old_password': 'WrongOldPass',
            'new_password1': 'Pass456!',
            'new_password2': 'Pass456!'
        })

        # stare hasło powinno nadal działać
        self.client.logout()
        login_success = self.client.login(username='testuser', password='Pass123!')
        self.assertTrue(login_success)