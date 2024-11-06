"""
Django settings for tracker project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-ac^0#la%7=9%2@vq)i@kk1yz%6zprm8pw(#+4zo65(oa76yivw'
DEBUG = True
ALLOWED_HOSTS = []  # Update this with your production domain/IP

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',    
    'complaints',
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

ROOT_URLCONF = 'tracker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # Add custom template directories if needed
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

WSGI_APPLICATION = 'tracker.wsgi.application'

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Specify custom user model
#AUTH_USER_MODEL = 'users.CustomUser'  # Uncomment this line to use your custom user model

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'pesamashinaniservices@gmail.com'
EMAIL_HOST_PASSWORD = 'gjch yrql wced cjxm'  # Use the App Password generated

# M-Pesa settings
CONSUMER_KEY = 'iUxIlMxhUAKzZeSCz6sWvHaOnE8vgZQAUozLAw4HvkSp0SRm'  # Your M-Pesa consumer key
CONSUMER_SECRET = 'tKuC8G9qsKiODjb2aBaW8cOkLpRJZsyTPQSetmAG37wtrvkuO8pBFB3kwxxD1bHb'  # Your M-Pesa consumer secret
POCHI_PHONE_NUMBER = '0758483179'  # Replace with your actual Pochi La Biashara phone number
TILL_NUMBER = 'your_till_number'  # Replace with your Pochi la Biashara till number if applicable

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_URL = '/static/'

# App-level static files
APP_STATIC_ROOT = os.path.join(BASE_DIR, 'complaints/static/')
STATICFILES_DIRS = [APP_STATIC_ROOT]

# Absolute filesystem path to the directory that will hold collected static files.
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
