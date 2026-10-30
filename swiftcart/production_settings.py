from .settings import *
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


# Ensure Django's static-file management commands are available in production.
INSTALLED_APPS = list(globals().get("INSTALLED_APPS", []))
if "django.contrib.staticfiles" not in INSTALLED_APPS:
    INSTALLED_APPS.append("django.contrib.staticfiles")
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

# THE LABEL GROUP PRODUCT IMAGE DELIVERY
# Make media/products discoverable as static/products during deployment.
# This does not change MEDIA_ROOT or customer-uploaded media delivery.

_label_product_media_root = BASE_DIR / "media"
_label_product_directory = _label_product_media_root / "products"

if not _label_product_directory.is_dir():
    raise RuntimeError(
        "Product image directory is missing: "
        + str(_label_product_directory)
    )

_label_static_directories = list(
    globals().get("STATICFILES_DIRS", [])
)

# Remove old mappings that point directly at media/products.
# Use the parent media directory so Django discovers products/... reliably.
_clean_static_directories = []

for entry in _label_static_directories:
    directory = (
        entry[1]
        if isinstance(entry, tuple) and len(entry) == 2
        else entry
    )

    try:
        resolved = Path(directory).resolve()
    except (TypeError, OSError):
        _clean_static_directories.append(entry)
        continue

    if resolved == _label_product_directory.resolve():
        continue

    _clean_static_directories.append(entry)

_media_root_already_registered = False

for entry in _clean_static_directories:
    directory = (
        entry[1]
        if isinstance(entry, tuple) and len(entry) == 2
        else entry
    )

    try:
        if Path(directory).resolve() == _label_product_media_root.resolve():
            _media_root_already_registered = True
            break
    except (TypeError, OSError):
        pass

if not _media_root_already_registered:
    _clean_static_directories.append(_label_product_media_root)

STATICFILES_DIRS = _clean_static_directories

# Redirect only product images. Other media URLs remain unchanged.
MIDDLEWARE = list(MIDDLEWARE)

_label_product_middleware = (
    "swiftcart.media_redirect.ProductMediaStaticRedirectMiddleware"
)

if _label_product_middleware not in MIDDLEWARE:
    _whitenoise_index = next(
        (
            index for index, middleware in enumerate(MIDDLEWARE)
            if middleware == "whitenoise.middleware.WhiteNoiseMiddleware"
        ),
        None
    )

    if _whitenoise_index is None:
        raise RuntimeError(
            "WhiteNoise middleware is missing from MIDDLEWARE."
        )

    MIDDLEWARE.insert(
        _whitenoise_index,
        _label_product_middleware
    )

# End THE LABEL GROUP PRODUCT IMAGE DELIVERY

