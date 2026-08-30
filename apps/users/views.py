from django import forms
from django.conf import settings
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
    UsernameField,
)
from django.shortcuts import render, redirect, resolve_url
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.utils.http import url_has_allowed_host_and_scheme

from .password_rules import rules_for_template
from .validators import USERNAME_HELP_TEXT, username_characters_validator

LOGIN_ATTEMPT_LIMIT = 5
LOGIN_ATTEMPT_WINDOW = 300  # sekundy

DEMO_LOCKED_MESSAGE = (
    'This is a shared demo account. Its username and password are published in the '
    'documentation, so they cannot be changed and the account cannot be deleted. '
    'Register your own account to use these options.'
)


def is_demo_account(user):
    demo_username = getattr(settings, 'DEMO_USERNAME', '')
    return bool(demo_username) and user.username.lower() == demo_username.lower()


class CustomUserCreationForm(UserCreationForm):

    email = forms.EmailField(
        required=False,
        label='Email (optional)',
        help_text='Only used to reset your password. Without it a forgotten '
                  'password cannot be recovered.',
        widget=forms.EmailInput(attrs={'autocomplete': 'email'}),
    )

    accept_terms = forms.BooleanField(
        required=True,
        label='I have read and accept the Terms of Service and Privacy Policy',
        error_messages={
            'required': 'You must accept the Terms of Service and Privacy Policy.'
        },
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].validators.append(username_characters_validator)
        self.fields['username'].help_text = USERNAME_HELP_TEXT

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'An account with this email address already exists.'
            )

        return email


class AccountDetailsForm(forms.ModelForm):

    email = forms.EmailField(
        required=False,
        label='Email (optional)',
        help_text='Used only to reset your password.',
        widget=forms.EmailInput(attrs={'autocomplete': 'email'}),
    )

    class Meta:
        model = User
        fields = ('username', 'email')
        field_classes = {'username': UsernameField}

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if not username:
            return username

        # nowy zestaw znaków tylko przy zmianie nazwy
        if username != self.instance.username:
            username_characters_validator(username)

        if User.objects.filter(
            username__iexact=username
        ).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This username is already taken.')

        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if email and User.objects.filter(
            email__iexact=email
        ).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                'An account with this email address already exists.'
            )

        return email


def _safe_redirect_target(request):
    # bez sprawdzenia hosta next byłby otwartym przekierowaniem
    target = request.POST.get('next') or request.GET.get('next')

    if target and url_has_allowed_host_and_scheme(
        target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return target

    return resolve_url(settings.LOGIN_REDIRECT_URL)


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()

            from apps.preferences.models import UserProfile
            UserProfile.objects.create(user=user)

            # konto właśnie powstało, więc nie ma po co odsyłać na logowanie
            login(request, user)
            messages.success(
                request,
                f'Welcome, {user.username}! Start by marking ingredients you '
                f'want to avoid.'
            )
            return redirect('profile')
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {
        'form': form,
        'password_rules': rules_for_template(),
    })


def login_view(request):
    cache_key = f"login_attempts_{request.META.get('REMOTE_ADDR', 'unknown')}"
    form = AuthenticationForm(request)

    if request.method == 'POST':
        attempts = cache.get(cache_key, 0)

        if attempts >= LOGIN_ATTEMPT_LIMIT:
            minutes = LOGIN_ATTEMPT_WINDOW // 60
            messages.error(
                request,
                f'Too many failed login attempts. Please try again in {minutes} minutes.'
            )
            return render(request, 'users/login.html', {
                'form': AuthenticationForm(request, data=request.POST),
                'next': request.POST.get('next', ''),
            })

        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            cache.delete(cache_key)
            login(request, form.get_user())
            return redirect(_safe_redirect_target(request))

        cache.set(cache_key, attempts + 1, LOGIN_ATTEMPT_WINDOW)

    return render(request, 'users/login.html', {
        'form': form,
        'next': request.POST.get('next') or request.GET.get('next', ''),
    })


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('index')


@login_required
@require_POST
def change_password(request):
    if is_demo_account(request.user):
        messages.error(request, DEMO_LOCKED_MESSAGE)
        return redirect('profile')

    form = PasswordChangeForm(user=request.user, data=request.POST)

    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Password changed successfully!')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)

    return redirect('profile')


@login_required
def update_account(request):
    if request.method == 'POST':
        if is_demo_account(request.user):
            messages.error(request, DEMO_LOCKED_MESSAGE)
            return redirect('profile')

        form = AccountDetailsForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, 'Username updated successfully!')
        else:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)

    return redirect('profile')


@login_required
@require_POST
def delete_account(request):
    if is_demo_account(request.user):
        messages.error(request, DEMO_LOCKED_MESSAGE)
        return redirect('profile')

    user = request.user
    logout(request)
    user.delete()
    messages.success(request, 'Your account has been deleted.')
    return redirect('index')