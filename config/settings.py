from pathlib import Path
from decouple import config
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

TESTING = 'test' in sys.argv

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

CSRF_TRUSTED_ORIGINS = [
    'https://incipreferences.app',
]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'apps.ingredients',
    'apps.cosmetics',
    'apps.users',
    'apps.preferences',
    'django_filters',
    'csp',
    'storages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
]

# odświeżanie przeglądarki przy zmianie plików, tylko lokalnie i tylko gdy
# pakiet jest zainstalowany (requirements-dev.txt)
if DEBUG:
    try:
        import django_browser_reload  # noqa: F401
    except ImportError:
        BROWSER_RELOAD_ENABLED = False
    else:
        BROWSER_RELOAD_ENABLED = True
        INSTALLED_APPS.append('django_browser_reload')
        MIDDLEWARE.append('django_browser_reload.middleware.BrowserReloadMiddleware')
else:
    BROWSER_RELOAD_ENABLED = False

USE_R2 = config('USE_R2', default=False, cast=bool)
R2_PUBLIC_URL = config('R2_PUBLIC_URL', default='') if USE_R2 else ''

CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ["'self'"],
        # 'wasm-unsafe-eval' jest dla skanera
        'script-src': ["'self'", "'unsafe-inline'", "'wasm-unsafe-eval'", 'https://cdn.jsdelivr.net'] + ([R2_PUBLIC_URL] if R2_PUBLIC_URL else []),
        'style-src': ["'self'", "'unsafe-inline'"] + ([R2_PUBLIC_URL] if R2_PUBLIC_URL else []),
        'img-src': ["'self'", 'data:'] + ([R2_PUBLIC_URL] if R2_PUBLIC_URL else []),
        'font-src': ["'self'"] + ([R2_PUBLIC_URL] if R2_PUBLIC_URL else []),
        'worker-src': ["'self'", 'blob:'],
        'connect-src': ["'self'", 'https://cdn.jsdelivr.net', 'https://tessdata.projectnaptha.com'],
    },
}

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/min',
        'user': '300/min',
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'apps.users.password_rules.PasswordComplexityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = "index"
LOGOUT_REDIRECT_URL = "index"

# poczta wychodząca, wyłącznie do resetu hasła. lokalnie wiadomości lądują
# w konsoli serwera, więc link da się przetestować bez SMTP
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend' if DEBUG
    else 'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL', default='INCI Preferences <noreply@incipreferences.app>'
)

PASSWORD_RESET_TIMEOUT = 60 * 60 * 24  # doba zamiast domyslnych 3 dni

DEMO_USERNAME = config('DEMO_USERNAME', default='testuser')

if USE_R2:
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'storages.backends.s3.S3Storage',
            'OPTIONS': {
                'access_key': config('R2_ACCESS_KEY_ID', default=''),
                'secret_key': config('R2_SECRET_ACCESS_KEY', default=''),
                'bucket_name': config('R2_BUCKET_NAME', default=''),
                'endpoint_url': f"https://{config('R2_ACCOUNT_ID', default='')}.r2.cloudflarestorage.com",
                'custom_domain': R2_PUBLIC_URL.replace('https://', '').replace('http://', ''),
                'location': 'static',
                'default_acl': None,
                'querystring_auth': False,
                'region_name': 'auto',
                'file_overwrite': True,
                'object_parameters': {'CacheControl': 'public, max-age=3600'},
            },
        },
    }
    STATIC_URL = f"{R2_PUBLIC_URL.rstrip('/')}/static/"
elif not DEBUG:
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

if not DEBUG and not TESTING:
    # Force HTTPS
    SECURE_SSL_REDIRECT = True
    # Proxy header
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # HSTS
    SECURE_HSTS_SECONDS = 31536000  # 1 rok
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Secure cookies
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Content security
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
