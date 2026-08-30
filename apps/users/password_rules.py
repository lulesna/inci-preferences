from django.core.exceptions import ValidationError

MIN_LENGTH = 8

# Lista wymagań pod polem hasła odhacza się na żywo, więc musi sprawdzać
# dokładnie to samo co walidator, stąd predykat i wzorzec dla JS obok siebie.
# \p{Ll} i \p{Lu} obejmują też ogonki, więc "ż" to mała litera, a "Ż" wielka
PASSWORD_RULES = [
    {
        'key': 'length',
        'text': f'at least {MIN_LENGTH} characters',
        'pattern': f'.{{{MIN_LENGTH},}}',
        'test': lambda password: len(password) >= MIN_LENGTH,
    },
    {
        'key': 'lowercase',
        'text': 'a lowercase letter',
        'pattern': r'\p{Ll}',
        'test': lambda password: any(char.islower() for char in password),
    },
    {
        'key': 'uppercase',
        'text': 'an uppercase letter',
        'pattern': r'\p{Lu}',
        'test': lambda password: any(char.isupper() for char in password),
    },
    {
        'key': 'digit',
        'text': 'a digit',
        'pattern': r'\d',
        'test': lambda password: any(char.isdigit() for char in password),
    },
]


def rules_for_template():
    # bez predykatów, żeby dało się to zserializować do JSON w szablonie
    return [
        {'key': rule['key'], 'text': rule['text'], 'pattern': rule['pattern']}
        for rule in PASSWORD_RULES
    ]


def missing_rules(password):
    return [rule for rule in PASSWORD_RULES if not rule['test'](password)]


# zastępuje MinimumLengthValidator
class PasswordComplexityValidator:

    def validate(self, password, user=None):
        missing = missing_rules(password)

        if missing:
            raise ValidationError(
                'This password must contain %(requirements)s.',
                code='password_too_simple',
                params={'requirements': ', '.join(rule['text'] for rule in missing)},
            )

    def get_help_text(self):
        return 'Your password must contain ' + ', '.join(
            rule['text'] for rule in PASSWORD_RULES
        ) + '.'
