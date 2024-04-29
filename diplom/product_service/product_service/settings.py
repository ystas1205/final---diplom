"""
Django settings for product_service project.

Generated by 'django-admin startproject' using Django 5.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
import os
from dotenv import load_dotenv

from tests.settings import BASE_DIR

from product_service.celery import app

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-0+@nln70lc=y)^dwmmutddelof&28s44dho=bv!xqc057+5ojk'
SECRET_KEY = os.getenv('SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True
DEBUG = os.getenv('DEBUG')
ALLOWED_HOSTS = ['*']
INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

# Application definition

INSTALLED_APPS = [
    'baton',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'oauth2_provider',
    'social_django',
    'rest_framework_social_oauth2',
    'rest_framework.authtoken',
    'drf_spectacular',
    'django_rest_passwordreset',
    'debug_toolbar',
    'backend',
    'django_celery_results',
    'import_export',
    'baton.autodiscover',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'product_service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'product_service.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.getenv('POSTGRES_ENGINE'),
        'NAME': os.getenv('POSTGRES_DB'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': os.getenv('POSTGRES_PORT'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD')
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

AUTH_USER_MODEL = 'backend.User'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# EMAIL_HOST = os.getenv('EMAIL_HOST'),
# EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER'),
# EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD'),
# EMAIL_PORT = os.getenv('EMAIL_PORT'),
# EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL'),
# SERVER_EMAIL = EMAIL_HOST_USER
EMAIL_HOST = 'smtp.mail.ru'
EMAIL_HOST_USER = 'ystas2019@mail.ru'
EMAIL_HOST_PASSWORD = '7zPkj6PxU7NUjngp6fhV'
EMAIL_PORT = '465'
EMAIL_USE_SSL = True
SERVER_EMAIL = EMAIL_HOST_USER

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {

    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 40,

    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',

    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',

    'DEFAULT_AUTHENTICATION_CLASSES': (

        'rest_framework.authentication.TokenAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework_social_oauth2.authentication.SocialAuthentication',
    ),

}
SOCIAL_AUTH_VK_OAUTH2_KEY = '51664963'
SOCIAL_AUTH_VK_OAUTH2_SECRET = '6gTT3qZUnOVhmrmdbLvf'
SOCIAL_AUTH_VK_OAUTH2_SCOPE = ['email']
SOCIAL_AUTH_VK_OAUTH2_EXTRA_PARAMS = {'fields': 'email', }
AUTHENTICATION_BACKENDS = (
    'social_core.backends.vk.VKOAuth2',
    'rest_framework_social_oauth2.backends.DjangoOAuth2',
    'django.contrib.auth.backends.ModelBackend',

)
DRFSO2_URL_NAMESPACE = 'social'

# SOCIAL_AUTH_VK_OAUTH2_SCOPE = ['email']
# SOCIAL_AUTH_VK_OAUTH2_EXTRA_PARAMS = {'fields': 'email', }

# SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
# SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
#     'fields': 'id, name, email'
# }


CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'

CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/1'

# CELERY_BROKER_URL: os.getenv('CELERY_BROKER_URL')
#
# CELERY_RESULT_BACKEND: os.getenv('CELERY_RESULT_BACKEND')

CELERY_CACHE_BACKEND = 'django-cache'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'redis://localhost:6379/1',
    }
}
SPECTACULAR_SETTINGS = {
    'TITLE': 'Сервис заказа розничных сетей API',
    'DESCRIPTION': 'Your project description',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # OTHER SETTINGS
}

# CELERY_TASK_ALWAYS_EAGER  = True
BATON = {
    # 'CHANGELIST_FILTERS_IN_MODAL': True,
    'CHANGELIST_FILTERS_ALWAYS_OPEN': True,
    'CHANGELIST_FILTERS_FORM': True,
    'COLLAPSABLE_USER_AREA': True,
    'MENU_ALWAYS_COLLAPSED': False,
    # 'MENU_TITLE': 'Menu',
    # 'MESSAGES_TOASTS': True,
    'GRAVATAR_DEFAULT_IMG': 'Blank',
    'GRAVATAR_ENABLED': True,
}
