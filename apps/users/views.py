from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.core.cache import cache

LOGIN_ATTEMPT_LIMIT = 5
LOGIN_ATTEMPT_WINDOW = 300  # sekundy


class CustomUserCreationForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, help_text='Unique username.')
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput, required=True)

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


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
        new_username = request.POST.get('username')
        user = request.user

        if User.objects.filter(username=new_username).exclude(id=user.id).exists():
            messages.error(request, 'This username is already taken.')
        else:
            user.username = new_username
            user.save()
            messages.success(request, 'Username updated successfully!')

    return redirect('profile')


@login_required
@require_POST
def delete_account(request):
    user = request.user
    logout(request)
    user.delete()
    messages.success(request, 'Your account has been deleted.')
    return redirect('index')