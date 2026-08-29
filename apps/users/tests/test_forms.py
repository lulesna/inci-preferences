from django.test import TestCase
from django.contrib.auth.models import User

from apps.users.views import CustomUserCreationForm


class CustomUserCreationFormTest(TestCase):

    def form_data(self, **overrides):
        data = {
            'username': 'nowyuser',
            'password1': 'ZlozoneHaslo123',
            'password2': 'ZlozoneHaslo123',
        }
        data.update(overrides)
        return data

    def test_valid_data_accepted(self):
        form = CustomUserCreationForm(data=self.form_data())
        self.assertTrue(form.is_valid())

    def test_duplicate_username_rejected(self):
        User.objects.create_user(username='zajety', password='pass12345')

        form = CustomUserCreationForm(data=self.form_data(username='zajety'))

        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_password_mismatch_rejected(self):
        form = CustomUserCreationForm(data=self.form_data(password2='InneHaslo123'))

        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_save_stores_hashed_password(self):
        form = CustomUserCreationForm(data=self.form_data())
        self.assertTrue(form.is_valid())

        user = form.save()

        self.assertNotEqual(user.password, 'ZlozoneHaslo123')
        self.assertTrue(user.check_password('ZlozoneHaslo123'))


class PasswordValidatorsTest(TestCase):

    def form_data(self, password):
        return {
            'username': 'nowyuser',
            'password1': password,
            'password2': password,
        }

    def assertPasswordRejected(self, password):
        form = CustomUserCreationForm(data=self.form_data(password))

        self.assertFalse(form.is_valid(), f'Hasło {password!r} powinno zostać odrzucone')
        self.assertIn('password2', form.errors)
        return form.errors['password2']

    def test_too_short_password_rejected(self):
        # MinimumLengthValidator, domyślnie minimum 8 znaków
        self.assertPasswordRejected('Ab1x')

    def test_common_password_rejected(self):
        # CommonPasswordValidator, lista 20 000 najpopularniejszych haseł
        self.assertPasswordRejected('password123')

    def test_numeric_password_rejected(self):
        # NumericPasswordValidator
        self.assertPasswordRejected('86753098421')

    def test_password_similar_to_username_rejected(self):
        # UserAttributeSimilarityValidator porównuje hasło z nazwą użytkownika
        self.assertPasswordRejected('nowyuser1')
