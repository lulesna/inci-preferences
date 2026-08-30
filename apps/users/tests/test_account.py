import re

from django.core import mail
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse

from apps.preferences.models import UserProfile


class RegistrationTest(TestCase):

    def setUp(self):
        cache.clear()
        self.client = Client()

    def post_registration(self, password, username='nowyuser', **extra):
        data = {
            'username': username,
            'password1': password,
            'password2': password,
            'accept_terms': 'on',
        }
        data.update(extra)
        return self.client.post(reverse('users:register'), data)

    def test_registration_logs_the_user_in(self):
        response = self.post_registration('ZlozoneHaslo123')

        self.assertRedirects(response, reverse('profile'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_registration_stores_optional_email(self):
        self.post_registration('ZlozoneHaslo123', email='ktos@example.com')

        self.assertEqual(
            User.objects.get(username='nowyuser').email, 'ktos@example.com'
        )

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


class LoginFlowTest(TestCase):

    def setUp(self):
        cache.clear()
        self.client = Client()
        User.objects.create_user(username='user1', password='ZlozoneHaslo123')

    def test_failed_login_keeps_the_username(self):
        # widok renderował szablon bez kontekstu, więc po literówce w haśle
        # użytkownik przepisywał również login
        response = self.client.post(reverse('users:login'), {
            'username': 'user1',
            'password': 'zle-haslo',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form']['username'].value(), 'user1')

    def test_login_redirects_to_next(self):
        response = self.client.post(
            reverse('users:login') + '?next=/favorites/',
            {'username': 'user1', 'password': 'ZlozoneHaslo123', 'next': '/favorites/'},
        )

        self.assertRedirects(response, '/favorites/')

    def test_login_ignores_external_next(self):
        # bez sprawdzenia hosta ten link wyrzuciłby zalogowanego na obcą domenę
        response = self.client.post(
            reverse('users:login'),
            {
                'username': 'user1',
                'password': 'ZlozoneHaslo123',
                'next': 'https://zlosliwa-domena.example/phish',
            },
        )

        self.assertRedirects(response, reverse('index'))

    def test_login_required_redirects_to_our_login_page(self):
        # bez LOGIN_URL Django kierowało na nieistniejące /accounts/login/
        response = self.client.get(reverse('profile'))

        self.assertRedirects(
            response, f"{reverse('users:login')}?next={reverse('profile')}"
        )

    def test_lockout_message_states_the_wait(self):
        for _ in range(5):
            self.client.post(reverse('users:login'), {
                'username': 'user1', 'password': 'zle-haslo',
            })

        response = self.client.post(reverse('users:login'), {
            'username': 'user1', 'password': 'ZlozoneHaslo123',
        })

        wiadomosci = [str(m) for m in response.context['messages']]
        self.assertTrue(any('5 minutes' in m for m in wiadomosci), wiadomosci)


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

    def test_new_username_must_use_allowed_characters(self):
        self.client.login(username='user1', password='pass12345')

        self.client.post(reverse('users:update_account'), {'username': 'jan.kowalski'})

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'user1')

    def test_hyphen_and_underscore_accepted(self):
        self.client.login(username='user1', password='pass12345')

        self.client.post(reverse('users:update_account'), {'username': 'lucja_lesna-99'})

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'lucja_lesna-99')

    def test_legacy_username_can_still_save_other_fields(self):
        # konto sprzed zawężenia znaków musi móc zapisać e-mail bez zmiany
        # nazwy, inaczej byłoby zablokowane
        stary = User.objects.create_user(username='jan.kowalski', password='pass12345')
        self.client.login(username='jan.kowalski', password='pass12345')

        self.client.post(reverse('users:update_account'), {
            'username': 'jan.kowalski',
            'email': 'jan@example.com',
        })

        stary.refresh_from_db()
        self.assertEqual(stary.username, 'jan.kowalski')
        self.assertEqual(stary.email, 'jan@example.com')

    def test_username_with_illegal_characters_rejected(self):
        self.client.login(username='user1', password='pass12345')

        self.client.post(reverse('users:update_account'), {'username': 'zla nazwa!'})

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'user1')


@override_settings(DEMO_USERNAME='testuser')
class DemoAccountProtectionTest(TestCase):

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


class PasswordResetTest(TestCase):

    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            username='user1', password='ZlozoneHaslo123', email='user1@example.com'
        )
        mail.outbox = []

    def request_reset(self, email):
        return self.client.post(reverse('users:password_reset'), {'email': email})

    def test_reset_email_sent_with_working_link(self):
        response = self.request_reset('user1@example.com')

        self.assertRedirects(response, reverse('users:password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)

        link = re.search(r'/users/password-reset/[\w-]+/[\w-]+/', mail.outbox[0].body)
        self.assertIsNotNone(link, mail.outbox[0].body)

        # Django przekierowuje z tokenu w URL-u na adres z 'set-password'
        response = self.client.get(link.group(), follow=True)
        self.assertTrue(response.context['validlink'])

    def test_full_reset_lets_user_log_in_with_new_password(self):
        self.request_reset('user1@example.com')
        link = re.search(
            r'/users/password-reset/[\w-]+/[\w-]+/', mail.outbox[0].body
        ).group()

        self.client.get(link, follow=True)
        response = self.client.post(
            self.client.get(link).headers['Location'],
            {'new_password1': 'CalkiemNoweHaslo9', 'new_password2': 'CalkiemNoweHaslo9'},
        )

        self.assertRedirects(response, reverse('users:password_reset_complete'))
        self.assertTrue(
            self.client.login(username='user1', password='CalkiemNoweHaslo9')
        )

    def test_unknown_email_does_not_reveal_anything(self):
        response = self.request_reset('nieznany@example.com')

        self.assertRedirects(response, reverse('users:password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)

    def test_account_without_email_gets_no_message(self):
        User.objects.create_user(username='bezmaila', password='ZlozoneHaslo123')

        response = self.request_reset('')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_new_password_must_pass_validators(self):
        self.request_reset('user1@example.com')
        link = re.search(
            r'/users/password-reset/[\w-]+/[\w-]+/', mail.outbox[0].body
        ).group()

        response = self.client.post(
            self.client.get(link).headers['Location'],
            {'new_password1': '12345', 'new_password2': '12345'},
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('ZlozoneHaslo123'))


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
