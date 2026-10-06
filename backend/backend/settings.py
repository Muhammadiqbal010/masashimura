from pathlib import Path
import os

from dotenv import load_dotenv

import cloudinary
import cloudinary.uploader
import cloudinary.api

# Load environment variables dari .env
load_dotenv()
# ========================
# BASE CONFIG
# ========================
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-ftxu0z)2z=ei553@4usfbx@*$037=ae8=8b+8bl(_%w*++t-uy'
DEBUG = False
ALLOWED_HOSTS = [
    'masashimura-backend.vercel.app',
    '.vercel.app',
]

load_dotenv(BASE_DIR / ".env")
# ========================
# CLOUDINARY
# ========================
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True,
)

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# ========================
# INSTALLED APPS
# ========================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken', # Wajib untuk TokenAuthentication
    'corsheaders',
    'accounts',
    'menu',
    'order',
    'homepage',
    'finance',
    'prediction',
    'promotions',
    'payments',
]

# ========================
# MIDDLEWARE
# ========================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ========================
# REST FRAMEWORK (DIPERBAIKI)
# ========================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication', # Sinkron dengan client.js
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated', # Semua API butuh login
    ],
    'DEFAULT_THROTTLE_RATES': {
        'reset_password': '5/hour',
        'login': '10/hour',          # <- baru: batasin brute-force login
        'admin_action': '30/hour',   # <- baru: batasin admin_reset_password & set-pin
    },
}

TOKEN_EXPIRE_HOURS = 24 * 1
# ========================
# SISANYA (JANGAN DIUBAH)
# ========================
ROOT_URLCONF = 'backend.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '6543'),
        'OPTIONS': {
            'sslmode': 'require',  # Wajib untuk Supabase
        },
    }
}

# ========================
# Midtrans
# ========================
MIDTRANS_SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY", "")
MIDTRANS_CLIENT_KEY = os.getenv("MIDTRANS_CLIENT_KEY", "")
MIDTRANS_IS_PRODUCTION = os.getenv("MIDTRANS_IS_PRODUCTION", "False") == "True"

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://masashimura.*\.vercel\.app$",
]
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'