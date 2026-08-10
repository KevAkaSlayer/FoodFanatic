"""Django settings for FoodFanatic."""

import os
from pathlib import Path

import environ

from django.core.exceptions import ImproperlyConfigured

from .database import build_database_config, resolve_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
IS_VERCEL = os.environ.get("VERCEL") == "1"
# Keep deployment-provided values before django-environ loads local .env files.
RUNTIME_ENVIRONMENT = dict(os.environ)

env = environ.Env(
    DEBUG=(bool, not IS_VERCEL),
    EMAIL_USE_TLS=(bool, True),
    SECURE_HSTS_INCLUDE_SUBDOMAINS=(bool, False),
    SECURE_HSTS_PRELOAD=(bool, False),
    SECURE_SSL_REDIRECT=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

DEBUG = env.bool("DEBUG")
_DEVELOPMENT_SECRET = "development-only-secret-key-change-before-deploying"
SECRET_KEY = env(
    "SECRET_KEY",
    default=env("DJANGO_SECRET_KEY", default=_DEVELOPMENT_SECRET),
)
if not DEBUG and SECRET_KEY == _DEVELOPMENT_SECRET:
    raise ImproperlyConfigured(
        "Set SECRET_KEY (or DJANGO_SECRET_KEY) when DEBUG is False."
    )

default_allowed_hosts = ["localhost", "127.0.0.1"]
if IS_VERCEL:
    default_allowed_hosts.append(".vercel.app")
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=default_allowed_hosts,
)
if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must be set when DEBUG is False.")
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=["https://*.vercel.app"] if IS_VERCEL else [],
)


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "crispy_bootstrap5",
    "menu",
    "order",
    "user",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "Food_Fanatic.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "Food_Fanatic.wsgi.application"


database_url = resolve_database_url(RUNTIME_ENVIRONMENT, env)
if database_url:
    DATABASES = {"default": build_database_config(database_url)}
else:
    if IS_VERCEL:
        raise ImproperlyConfigured(
            "DATABASE_URL or POSTGRES_URL must point to persistent PostgreSQL "
            "on Vercel."
        )
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", default="Asia/Dhaka")

USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]


def runtime_or_file_environment(name, default=""):
    return RUNTIME_ENVIRONMENT.get(name) or env(name, default=default)


SUPABASE_URL = runtime_or_file_environment("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = runtime_or_file_environment("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_STORAGE_BUCKET = runtime_or_file_environment(
    "SUPABASE_STORAGE_BUCKET", default="foodfanatic-media"
)
SUPABASE_STORAGE_ENABLED = bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)

if SUPABASE_STORAGE_ENABLED:
    MEDIA_URL = (
        f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/public/"
        f"{SUPABASE_STORAGE_BUCKET}/"
    )
    STORAGES = {
        "default": {
            "BACKEND": "Food_Fanatic.storage.SupabaseStorage",
            "OPTIONS": {
                "url": SUPABASE_URL,
                "key": SUPABASE_SERVICE_ROLE_KEY,
                "bucket_name": SUPABASE_STORAGE_BUCKET,
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    MEDIA_URL = env("MEDIA_URL", default="/media/")
    MEDIA_ROOT = env.path("MEDIA_ROOT", default=BASE_DIR / "media")
    STORAGES = {
        "default": {
            "BACKEND": "Food_Fanatic.storage.CompressedFileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

# Menu photography is displayed in cards a few hundred pixels wide, so uploads
# are capped well below the multi-megapixel originals cameras produce.
IMAGE_MAX_WIDTH = env.int("IMAGE_MAX_WIDTH", default=1200)
IMAGE_QUALITY = env.int("IMAGE_QUALITY", default=82)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"

EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS")
EMAIL_HOST_USER = env(
    "EMAIL_HOST_USER",
    default=env("EMAIL", default=""),
)
EMAIL_HOST_PASSWORD = env(
    "EMAIL_HOST_PASSWORD",
    default=env("EMAIL_PASSWORD", default=""),
)
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default="FoodFanatic <no-reply@example.com>",
)

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT")
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS")
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"

from django.contrib import messages

MESSAGE_TAGS = {
    messages.DEBUG: "alert-info",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}
