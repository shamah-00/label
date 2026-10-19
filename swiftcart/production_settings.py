"""
Production settings for The Label Group.

Required environment variables:
DJANGO_SECRET_KEY
DJANGO_ALLOWED_HOSTS

Optional:
DJANGO_CSRF_TRUSTED_ORIGINS
DJANGO_SECURE_HSTS_SECONDS

Do not activate these settings until the production environment is configured.
"""
import os
from .settings import *

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
        "Production requires DJANGO_ALLOWED_HOSTS with your actual domain."
    )

DEBUG = False

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

# Enable HSTS only after HTTPS is verified on the production domain.
SECURE_HSTS_SECONDS = int(
    os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0")
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

STATIC_ROOT = BASE_DIR / "staticfiles"

# Configure proxy SSL headers only according to your hosting provider's
# documented reverse-proxy setup. Do not guess this configuration.