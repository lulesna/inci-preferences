from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse

from apps.preferences.models import UserProfile


class RegistrationTest(TestCase):

    def setUp(self):
        cache.clear()
        self.client = Client()

    def post_registration(self, password, username='nowyuser'):
        return self.client.post(reverse('users:register'), {
            'username': username,
            'password1': password,
            'password2': password,
            'accept_terms': 'on',
        })

    def test_registration_creates_user_with_profile(self):
        response = self.post_registration('ZlozoneHaslo123')

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='nowyuser')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_weak_password_does_not_create_account(self):
        response = self.post_registration('12345')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='nowyuser').exists())

    def test_registration_without_accepting_terms_rejected(self):
        response = self.client.post(reverse('users:register'), {
            'username': 'nowyuser',
            'password1': 'ZlozoneHaslo123',
            'password2': 'ZlozoneHaslo123',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='nowyuser').exists())


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
        self.client.login(username='user1', password='pass12345')

        self.client.post(reverse('users:update_account'), {'username': 'user1'})

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'user1')

    def test_anonymous_user_cannot_change_username(self):
        self.client.post(reverse('users:update_account'), {'username': 'przejete'})

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'user1')

    def test_username_differing_only_in_case_rejected(self):
        # "ZAJETY" i "zajety" to ta sama nazwa
        self.client.login(username='user1', password='pass12345')

        self.client.post(reverse('users:update_account'), {'username': 'ZAJETY'})

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'user1')

    def test_changing_case_of_own_username_allowed(self):
        self.client.login(username='user1', password='pass12345')

        self.client.post(reverse('users:update_account'), {'username': 'USER1'})

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'USER1')

    def test_missing_username_field_does_not_crash(self):
        self.client.login(username='user1', password='pass12345')

        response = self.client.post(reverse('users:update_account'), {})

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'user1')

    def test_empty_username_rejected(self):
        self.client.login(username='user1', password='pass12345')

        self.client.post(reverse('users:update_account'), {'username': ''})

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'user1')

    def test_username_with_illegal_characters_rejected(self):
        self.client.login(username='user1', password='pass12345')

        self.client.post(reverse('users:update_account'), {'username': 'zla nazwa!'})

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'user1')


@override_settings(DEMO_USERNAME='testuser')
class DemoAccountProtectionTest(TestCase):
    """Konto pokazowe ma publiczne dane logowania (README), więc nikt nie może
    go przejąć ani usunąć."""

    def setUp(self):
        cache.clear()
        self.client = Client()
        self.demo = User.objects.create_user(username='testuser', password='testuser')
        self.client.login(username='testuser', password='testuser')

    def test_username_cannot_be_changed(self):
        self.client.post(reverse('users:update_account'), {'username': 'przejete'})

        self.demo.refresh_from_db()
        self.assertEqual(self.demo.username, 'testuser')

    def test_password_cannot_be_changed(self):
        self.client.post(reverse('users:change_password'), {
            'old_password': 'testuser',
            'new_password1': 'NoweHaslo12345',
            'new_password2': 'NoweHaslo12345',
        })

        self.demo.refresh_from_db()
        self.assertTrue(self.demo.check_password('testuser'))

    def test_account_cannot_be_deleted(self):
        self.client.post(reverse('users:delete_account'))

        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_protection_is_case_insensitive(self):
        # Nazwy różniące się wielkością liter to to samo konto, więc ochrona
        # nie może zależeć od tego, jak zapisano ją w ustawieniach.
        User.objects.filter(pk=self.demo.pk).update(username='TestUser')

        self.client.post(reverse('users:update_account'), {'username': 'przejete'})

        self.demo.refresh_from_db()
        self.assertEqual(self.demo.username, 'TestUser')

    def test_regular_account_is_unaffected(self):
        zwykly = User.objects.create_user(username='zwykly', password='pass12345')
        self.client.login(username='zwykly', password='pass12345')

        self.client.post(reverse('users:update_account'), {'username': 'nowanazwa'})

        zwykly.refresh_from_db()
        self.assertEqual(zwykly.username, 'nowanazwa')


@override_settings(DEMO_USERNAME='')
class DemoProtectionDisabledTest(TestCase):

    def test_empty_setting_disables_protection(self):
        cache.clear()
        user = User.objects.create_user(username='testuser', password='pass12345')
        client = Client()
        client.login(username='testuser', password='pass12345')

        client.post(reverse('users:update_account'), {'username': 'nowanazwa'})

        user.refresh_from_db()
        self.assertEqual(user.username, 'nowanazwa')


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
