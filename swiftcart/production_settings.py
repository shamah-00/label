"""
Production settings for The Label Group on Railway.

Required Railway variables:
DJANGO_SECRET_KEY
DJANGO_ALLOWED_HOSTS
DATABASE_URL

Optional:
DJANGO_CSRF_TRUSTED_ORIGINS
DJANGO_SECURE_HSTS_SECONDS
DATABASE_SSL_REQUIRE
"""

import os
import dj_database_url

from .settings import *

# Production must never silently fall back to temporary SQLite storage.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "").strip()

if not SECRET_KEY or SECRET_KEY.startswith("django-insecure-"):
    raise RuntimeError(
        "Production requires a strong DJANGO_SECRET_KEY environment variable."
    )

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

if not ALLOWED_HOSTS:
    raise RuntimeError(
        "Production requires DJANGO_ALLOWED_HOSTS with the actual hostname."
    )

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if not DATABASE_URL:
    raise RuntimeError(
        "Production requires DATABASE_URL connected to Railway PostgreSQL."
    )

DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=os.environ.get(
            "DATABASE_SSL_REQUIRE", "false"
        ).strip().lower() == "true",
    )
}

DEBUG = False

# WhiteNoise serves collected Django static files.
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    security_middleware = "django.middleware.security.SecurityMiddleware"
    if security_middleware not in MIDDLEWARE:
        raise RuntimeError("Django SecurityMiddleware is missing.")

    MIDDLEWARE.insert(
        MIDDLEWARE.index(security_middleware) + 1,
        "whitenoise.middleware.WhiteNoiseMiddleware",
    )

STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Railway terminates HTTPS at its proxy.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "DJANGO_CSRF_TRUSTED_ORIGINS", ""
    ).split(",")
    if origin.strip()
]

# Enable HSTS only after production HTTPS has been verified.
SECURE_HSTS_SECONDS = int(
    os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0")
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False


# Public product uploads are served by the Django media URL route.
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Trusted HTTPS origin for The Label Group Railway deployment.
CSRF_TRUSTED_ORIGINS = list(globals().get("CSRF_TRUSTED_ORIGINS", [])) + ["https://web-production-d1e74.up.railway.app"]
