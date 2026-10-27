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
# SECRET_KEY WAJIB dari environment (Vercel -> Settings -> Environment Variables).
# Sengaja tanpa default: kalau lupa diisi, aplikasi gagal start (lebih aman
# daripada diam-diam jalan dengan key yang bisa ditebak).
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
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
        'payment_create': '10/min',  # per order_number (lihat payments/throttles.py)
        'payment_status': '60/min',  # per order_number; polling frontend = 30/min
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
MIDTRANS_SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY", "").strip()
MIDTRANS_CLIENT_KEY = os.getenv("MIDTRANS_CLIENT_KEY", "").strip()
MIDTRANS_IS_PRODUCTION = os.getenv("MIDTRANS_IS_PRODUCTION", "False").strip().lower() == "true"
# Penyedia QRIS untuk QR di POS: "gopay" (bawaan) atau "airpay shopee". Ikuti yang AKTIF di akun Midtrans lo.
MIDTRANS_QRIS_ACQUIRER = os.getenv("MIDTRANS_QRIS_ACQUIRER", "gopay").strip() or "gopay"

# Notifikasi pesanan web ke Telegram (opsional). Kosong = nonaktif.
# TELEGRAM_CHAT_ID boleh beberapa, dipisah koma (mis. chat pribadi + grup).
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
ADMIN_ORDERS_URL = os.getenv("ADMIN_ORDERS_URL", "https://masashimura.vercel.app/admin/orders").strip()

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