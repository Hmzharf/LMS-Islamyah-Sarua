"""
Django settings for library_system project.
"""
"""
Django settings for library_system project.
"""

from pathlib import Path
import os

# ⭐ LOAD .env DI SINI (PALING ATAS)
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Helper function
def get_env(key, default=None, cast=None):
    value = os.getenv(key, default)
    if value is None:
        return default
    if cast:
        if cast == bool:
            return str(value).lower() in ('true', '1', 'yes', 'on')
        elif cast == int:
            return int(value)
    return value

 
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

# Helper function untuk baca environment variables
def get_env(key, default=None, cast=None):
    """Get environment variable with optional type casting"""
    value = os.getenv(key, default)
    
    if value is None:
        return default
    
    if cast:
        if cast == bool:
            return str(value).lower() in ('true', '1', 'yes', 'on')
        elif cast == int:
            return int(value)
        elif cast == float:
            return float(value)
        return cast(value)
    
    return value


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = get_env('DEBUG', default='True', cast=bool)

ALLOWED_HOSTS = get_env('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Local apps
    'users',
    'books',
    'loans',
    'librarian',
    'reports',

    # Celery apps
    'django_celery_beat',
    'django_celery_results',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'library_system.urls'

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
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'library_system.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_env('DB_NAME', default='perpustakaan_db'),
        'USER': get_env('DB_USER', default=''),
        'PASSWORD': get_env('DB_PASSWORD', default=''),
        'HOST': get_env('DB_HOST', default='localhost'),
        'PORT': get_env('DB_PORT', default='5432'),
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.CustomUser'

# Login settings
LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'librarian:dashboard'
LOGOUT_REDIRECT_URL = 'home'

# Messages
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Session settings
SESSION_COOKIE_AGE = 1800  # 30 minutes
SESSION_SAVE_EVERY_REQUEST = True


# ========== CELERY CONFIGURATION ==========

# Celery Broker (Redis)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'

# Celery Settings
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Jakarta'
CELERY_ENABLE_UTC = False

# Celery Beat Schedule (Periodic Tasks)
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Task 1: Kirim reminder setiap hari jam 08:00
    'send-due-date-reminders': {
        'task': 'loans.tasks.send_due_date_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
    
    # Task 2: Kirim notifikasi keterlambatan setiap hari jam 09:00
    'send-overdue-notifications': {
        'task': 'loans.tasks.send_overdue_notifications',
        'schedule': crontab(hour=9, minute=0),
    },
    
    # Task 3: Update status peminjaman setiap jam
    'update-loan-status': {
        'task': 'loans.tasks.update_loan_status',
        'schedule': crontab(minute=0),
    },
}


# ========== EMAIL CONFIGURATION ==========

# Email Backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = get_env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = get_env('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = get_env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = get_env('EMAIL_HOST_PASSWORD', default='')

# Default From Email (dengan nama pengirim)
_default_from_email = get_env('DEFAULT_FROM_EMAIL', default='noreply@perpustakaan.com')
DEFAULT_FROM_EMAIL = f'Perpustakaan Sekolah <{_default_from_email}>'

# Admin emails
ADMINS = [
    ('Admin Perpustakaan', get_env('ADMIN_EMAIL', default='admin@perpustakaan.com')),
]