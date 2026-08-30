from django.core.exceptions import ValidationError
from django.test import TestCase
from django.contrib.auth.models import User

from apps.users.password_rules import (
    PASSWORD_RULES,
    PasswordComplexityValidator,
    missing_rules,
    rules_for_template,
)
from apps.users.validators import username_characters_validator
from apps.users.views import CustomUserCreationForm


class CustomUserCreationFormTest(TestCase):

    def form_data(self, **overrides):
        data = {
            'username': 'nowyuser',
            'password1': 'ZlozoneHaslo123',
            'password2': 'ZlozoneHaslo123',
            'accept_terms': 'on',
        }
        data.update(overrides)
        return data

    def test_valid_data_accepted(self):
        form = CustomUserCreationForm(data=self.form_data())
        self.assertTrue(form.is_valid())

    def test_email_is_optional(self):
        form = CustomUserCreationForm(data=self.form_data())

        self.assertTrue(form.is_valid())
        self.assertEqual(form.save().email, '')

    def test_duplicate_email_rejected(self):
        User.objects.create_user(
            username='ktos', password='pass12345', email='zajety@example.com'
        )

        form = CustomUserCreationForm(data=self.form_data(email='ZAJETY@example.com'))

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_username_charset_restricted(self):
        # Django dopuszcza domyślnie kropkę, małpę i plus, my nie
        for nazwa in ['jan.kowalski', 'user@domena', 'a+b', 'ze spacja', 'wykrzyknik!']:
            with self.subTest(nazwa=nazwa):
                form = CustomUserCreationForm(data=self.form_data(username=nazwa))

                self.assertFalse(form.is_valid(), f'{nazwa!r} powinno zostać odrzucone')
                self.assertIn('username', form.errors)

    def test_username_allows_letters_digits_hyphen_underscore(self):
        for nazwa in ['lucja', 'Lucja99', 'lucja-lesna', 'lucja_lesna', 'zolw']:
            with self.subTest(nazwa=nazwa):
                form = CustomUserCreationForm(data=self.form_data(username=nazwa))

                self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_username_allows_polish_letters(self):
        # \w obejmuje litery Unicode, więc ogonki przechodzą
        form = CustomUserCreationForm(data=self.form_data(username='łucja_leśna'))

        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_surrounding_whitespace_is_stripped(self):
        # CharField obcina białe znaki, więc do walidatora trafia już "lucja"
        form = CustomUserCreationForm(data=self.form_data(username='  lucja\n'))

        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(form.cleaned_data['username'], 'lucja')

    def test_terms_must_be_accepted(self):
        data = self.form_data()
        del data['accept_terms']

        form = CustomUserCreationForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('accept_terms', form.errors)

    def test_all_errors_reported_in_one_pass(self):
        # brak zgody przerywał walidację reszty, więc o słabym haśle
        # użytkownik dowiadywał się dopiero przy drugim zgłoszeniu
        data = self.form_data(password1='12345', password2='12345')
        del data['accept_terms']

        form = CustomUserCreationForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('accept_terms', form.errors)
        self.assertIn('password2', form.errors)

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
            'accept_terms': 'on',
        }

    def assertPasswordRejected(self, password):
        form = CustomUserCreationForm(data=self.form_data(password))

        self.assertFalse(form.is_valid(), f'Hasło {password!r} powinno zostać odrzucone')
        self.assertIn('password2', form.errors)
        return form.errors['password2']

    def test_too_short_password_rejected(self):
        self.assertPasswordRejected('Ab1x')

    def test_common_password_rejected(self):
        # CommonPasswordValidator, lista 20 000 najpopularniejszych haseł
        self.assertPasswordRejected('password123')

    def test_numeric_password_rejected(self):
        self.assertPasswordRejected('86753098421')

    def test_password_similar_to_username_rejected(self):
        # UserAttributeSimilarityValidator porównuje hasło z nazwą użytkownika
        self.assertPasswordRejected('nowyuser1')

    def test_password_without_digit_rejected(self):
        self.assertPasswordRejected('BezZadnejCyfry')

    def test_password_without_uppercase_rejected(self):
        self.assertPasswordRejected('bez wielkich 7')

    def test_password_without_lowercase_rejected(self):
        self.assertPasswordRejected('BEZ MALYCH 7')


class UsernameValidatorTest(TestCase):
    # sam walidator, bez formularza obcinającego białe znaki

    def assertRejected(self, nazwa):
        with self.assertRaises(ValidationError, msg=f'{nazwa!r} powinno zostać odrzucone'):
            username_characters_validator(nazwa)

    def test_rejects_characters_django_would_allow(self):
        for nazwa in ['jan.kowalski', 'user@domena', 'a+b']:
            with self.subTest(nazwa=nazwa):
                self.assertRejected(nazwa)

    def test_rejects_embedded_newline(self):
        self.assertRejected('jan\n')

    def test_rejects_empty_value(self):
        self.assertRejected('')

    def test_accepts_allowed_characters(self):
        for nazwa in ['jan', 'Jan99', 'a-b_c', 'łoś']:
            with self.subTest(nazwa=nazwa):
                username_characters_validator(nazwa)


class PasswordRulesConsistencyTest(TestCase):
    # lista pokazywana użytkownikowi musi zgadzać się z walidatorem

    def test_every_displayed_rule_is_enforced(self):
        # puste hasło łamie wszystkie reguły naraz
        self.assertEqual(
            [rule['key'] for rule in missing_rules('')],
            [rule['key'] for rule in PASSWORD_RULES],
        )

    def test_compliant_password_passes_every_rule(self):
        self.assertEqual(missing_rules('ZlozoneHaslo123'), [])

    def test_template_rules_expose_key_text_and_pattern(self):
        for rule in rules_for_template():
            self.assertEqual(set(rule), {'key', 'text', 'pattern'})

    def test_validator_names_the_missing_requirement(self):
        with self.assertRaises(ValidationError) as caught:
            PasswordComplexityValidator().validate('bezcyfryiwielkich')

        message = ' '.join(caught.exception.messages)
        self.assertIn('an uppercase letter', message)
        self.assertIn('a digit', message)
        self.assertNotIn('a lowercase letter', message)
