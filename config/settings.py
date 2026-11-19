
"""
Django settings for SoloSync.
Configuração para desenvolvimento local, Vercel e Microsoft Azure.
"""

from pathlib import Path
import os
import secrets
import sys

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


<<<<<<< HEAD
def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}
=======
# SEGURANÇA

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-local-development-only-change-me'
)

DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.vercel.app',
    '.azurewebsites.net',
]
>>>>>>> d99451e41c9010e9e70faa2f633edfd594b0a1de

# Permite adicionar outros domínios pelo ambiente
extra_hosts = os.environ.get('ALLOWED_HOSTS', '')
if extra_hosts:
    ALLOWED_HOSTS += [
        host.strip()
        for host in extra_hosts.split(',')
        if host.strip()
    ]

<<<<<<< HEAD
DEBUG = env_bool('DEBUG', True)

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError('SECRET_KEY deve ser definida por variável de ambiente em produção.')
    # Chave temporária em memória apenas para desenvolvimento local.
    SECRET_KEY = secrets.token_urlsafe(64)

ALLOWED_HOSTS = [host.strip() for host in os.getenv(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1',
).split(',') if host.strip()] 

CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv(
    'CSRF_TRUSTED_ORIGINS',
    'http://localhost,http://127.0.0.1',
).split(',') if origin.strip()] 
=======
CSRF_TRUSTED_ORIGINS = [
    'https://*.vercel.app',
    'https://*.azurewebsites.net',
]

extra_csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if extra_csrf_origins:
    CSRF_TRUSTED_ORIGINS += [
        origin.strip()
        for origin in extra_csrf_origins.split(',')
        if origin.strip()
    ]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG


# APLICATIVOS
>>>>>>> d99451e41c9010e9e70faa2f633edfd594b0a1de

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]


# MIDDLEWARE

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# URLS E TEMPLATES

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

<<<<<<< HEAD
SQLITE_PATH = Path(os.getenv('SQLITE_PATH', str(BASE_DIR / 'db.sqlite3'))).expanduser()
SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{SQLITE_PATH}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

=======

# BANCO DE DADOS

# Usa PostgreSQL quando DATABASE_URL estiver configurada.
# Caso contrário, utiliza SQLite para desenvolvimento local.

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# VALIDAÇÃO DE SENHAS

>>>>>>> d99451e41c9010e9e70faa2f633edfd594b0a1de
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

<<<<<<< HEAD
=======

# IDIOMA E FUSO HORÁRIO

>>>>>>> d99451e41c9010e9e70faa2f633edfd594b0a1de
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

<<<<<<< HEAD
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
=======

# ARQUIVOS ESTÁTICOS

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

>>>>>>> d99451e41c9010e9e70faa2f633edfd594b0a1de
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.getenv('MEDIA_ROOT', str(BASE_DIR / 'media'))).expanduser()
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

<<<<<<< HEAD
if not DEBUG:
    SECURE_SSL_REDIRECT = False if 'test' in sys.argv else env_bool('SECURE_SSL_REDIRECT', True)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Lax'
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
=======
# EMAIL
>>>>>>> d99451e41c9010e9e70faa2f633edfd594b0a1de

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

<<<<<<< HEAD
# Sobrescreve o backend em produção.
if not DEBUG:
    EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'webmaster@localhost')
=======

# AUTENTICAÇÃO
>>>>>>> d99451e41c9010e9e70faa2f633edfd594b0a1de

LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'
