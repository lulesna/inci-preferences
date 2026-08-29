from django import forms
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm, UsernameField
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_POST
from django.core.cache import cache

LOGIN_ATTEMPT_LIMIT = 5
LOGIN_ATTEMPT_WINDOW = 300  # sekundy

DEMO_LOCKED_MESSAGE = (
    'This is a shared demo account. Its username and password are published in the '
    'documentation, so they cannot be changed and the account cannot be deleted. '
    'Register your own account to use these options.'
)


def is_demo_account(user):
    """Czy to konto pokazowe, którego dane logowania są publiczne.

    Login i hasło konta demo są podane w README, więc każdy odwiedzający mógłby
    je przejąć, zmieniając hasło, albo zepsuć link w dokumentacji, zmieniając
    nazwę. Widoki modyfikujące konto sprawdzają ten warunek przed zapisem.
    """
    demo_username = getattr(settings, 'DEMO_USERNAME', '')
    return bool(demo_username) and user.username.lower() == demo_username.lower()


class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)


class UsernameChangeForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('username',)
        field_classes = {'username': UsernameField}

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if username and User.objects.filter(
            username__iexact=username
        ).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This username is already taken.')

        return username


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if not request.POST.get('accept_terms'):
            messages.error(request, 'You must accept the Terms of Service and Privacy Policy.')
        elif form.is_valid():
            user = form.save()

            from apps.preferences.models import UserProfile
            UserProfile.objects.create(user=user)

            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('users:login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        cache_key = f'login_attempts_{ip}'
        attempts = cache.get(cache_key, 0)

        if attempts >= LOGIN_ATTEMPT_LIMIT:
            messages.error(request, 'Too many failed login attempts. Please try again in a few minutes.')
            return render(request, 'users/login.html')

        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            cache.delete(cache_key)
            login(request, user)
            return redirect('index')
        else:
            cache.set(cache_key, attempts + 1, LOGIN_ATTEMPT_WINDOW)
            messages.error(request, 'Invalid username or password')

    return render(request, 'users/login.html')


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

        form = UsernameChangeForm(request.POST, instance=request.user)

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