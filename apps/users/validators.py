from django.core.validators import RegexValidator

# Django dopuszcza domyślnie [\w.@+-], ale my zawężamy do liter, cyfr, - i _
# \w łapie też ogonki, więc "żółw_1" przechodzi. \Z zamiast $, bo $ przepuszcza
# nazwę zakończoną znakiem nowej linii.
USERNAME_REGEX = r'^[\w-]+\Z'

USERNAME_HELP_TEXT = 'Letters, digits, hyphen and underscore only.'

username_characters_validator = RegexValidator(
    regex=USERNAME_REGEX,
    message='Username may contain only letters, digits, hyphens and underscores.',
    code='invalid_username_characters',
)
