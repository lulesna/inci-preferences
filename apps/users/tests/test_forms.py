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

        # Hasło nie może wylądować w bazie otwartym tekstem — save() nadpisuje
        # je wynikiem set_password().
        self.assertNotEqual(user.password, 'ZlozoneHaslo123')
        self.assertTrue(user.check_password('ZlozoneHaslo123'))
