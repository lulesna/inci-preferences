from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse


class LogoutTest(TestCase):

    def setUp(self):
        cache.clear()
        self.client = Client()
        User.objects.create_user(username='user1', password='pass12345')

    def test_logout_clears_session(self):
        self.client.login(username='user1', password='pass12345')
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.get(reverse('users:logout'))

        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)


class UpdateAccountTest(TestCase):

    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(username='user1', password='pass12345')
        User.objects.create_user(username='zajety', password='pass12345')

    def test_username_changed(self):
        self.client.login(username='user1', password='pass12345')

        response = self.client.post(reverse('users:update_account'), {'username': 'nowanazwa'})

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'nowanazwa')

    def test_username_taken_by_someone_else_rejected(self):
        self.client.login(username='user1', password='pass12345')

        self.client.post(reverse('users:update_account'), {'username': 'zajety'})

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'user1')

    def test_keeping_own_username_is_not_a_conflict(self):
        # Wykluczenie własnego id w zapytaniu sprawia, że wysłanie
        # niezmienionej nazwy nie jest traktowane jako duplikat.
        self.client.login(username='user1', password='pass12345')

        self.client.post(reverse('users:update_account'), {'username': 'user1'})

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'user1')

    def test_anonymous_user_cannot_change_username(self):
        self.client.post(reverse('users:update_account'), {'username': 'przejete'})

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'user1')


class DeleteAccountTest(TestCase):

    def setUp(self):
        cache.clear()
        self.client = Client()
        User.objects.create_user(username='user1', password='pass12345')

    def test_post_deletes_account(self):
        self.client.login(username='user1', password='pass12345')

        response = self.client.post(reverse('users:delete_account'))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username='user1').exists())

    def test_get_does_not_delete_account(self):
        self.client.login(username='user1', password='pass12345')

        response = self.client.get(reverse('users:delete_account'))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(User.objects.filter(username='user1').exists())

    def test_anonymous_user_cannot_delete_account(self):
        self.client.post(reverse('users:delete_account'))

        self.assertTrue(User.objects.filter(username='user1').exists())
