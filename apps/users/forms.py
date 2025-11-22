from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

        # Możesz też dodać placeholder lub zmienić label
        self.fields['username'].widget.attrs.update({'placeholder': 'Nazwa użytkownika'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Hasło'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Powtórz hasło'})

    def add_error(self, field, error):
        super().add_error(field, error)
        if field == 'password1' or field == 'password2':
            from django.contrib.auth.password_validation import password_validators_help_texts
            self.fields['password1'].help_text = password_validators_help_texts()

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')