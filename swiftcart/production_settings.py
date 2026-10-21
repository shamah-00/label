"""
Production settings for The Label Group on Railway.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
DEBUG = False

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS if h.strip()]

RAILWAY_STATIC_URL = os.environ.get("RAILWAY_STATIC_URL", "")
if RAILWAY_STATIC_URL:
    from urllib.parse import urlparse
    parsed_url = urlparse(RAILWAY_STATIC_URL)
    if parsed_url.hostname and parsed_url.hostname not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(parsed_url.hostname)

if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = [
        ".railway.app",
        "localhost",
        "127.0.0.1",
    ]

for domain in ["thelabelgroup.us.com", "www.thelabelgroup.us.com"]:
    if domain not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(domain)

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is missing or empty in production.")

import dj_database_url
DATABASES = {
    "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)
}

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

CSRF_TRUSTED_ORIGINS = list(globals().get("CSRF_TRUSTED_ORIGINS", [])) + [
    "https://web-production-d1e74.up.railway.app"
]

for domain in ["thelabelgroup.us.com", "www.thelabelgroup.us.com"]:
    origin = f"https://{domain}"
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(CSRF_TRUSTED_ORIGINS))
