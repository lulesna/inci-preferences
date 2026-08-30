from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .password_rules import rules_for_template

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('update-account/', views.update_account, name='update_account'),
    path('change-password/', views.change_password, name='change_password'),
    path('delete-account/', views.delete_account, name='delete_account'),

    # cztery kroki resetu hasła na widokach Django, z własnymi szablonami
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='users/password_reset.html',
            email_template_name='users/password_reset_email.txt',
            subject_template_name='users/password_reset_subject.txt',
            success_url=reverse_lazy('users:password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'password-reset/sent/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'password-reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html',
            success_url=reverse_lazy('users:password_reset_complete'),
            extra_context={'password_rules': rules_for_template()},
        ),
        name='password_reset_confirm',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
]
