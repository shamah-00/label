import os
from pathlib import Path


from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


SECRET_KEY = 'django-insecure-^kz!$&aquc9r8eyj%%p2ajai%q8#92+*i#xj3$m@0*#k*sz=rh'


DEBUG = True


ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost,web-production-d1e74.up.railway.app,web-production-74ca41.up.railway.app"
    ).split(",")
    if host.strip()
]
if "thelabelgroup.us.com" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("thelabelgroup.us.com")


CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "https://web-production-d1e74.up.railway.app,https://web-production-74ca41.up.railway.app"
    ).split(",")
    if origin.strip()
]
if "https://thelabelgroup.us.com" not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append("https://thelabelgroup.us.com")


INSTALLED_APPS = [
    'company_orders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'products',
    'staff',
]


MIDDLEWARE = [

    'staff.dashboard_repair.DashboardCountsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'swiftcart.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'libraries': {
                'product_specifications': 'products.templatetags.product_specifications',
            },
            'context_processors': [
                
                'products.context_processors.site_settings',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'swiftcart.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Nairobi'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'


MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'






# Production static-file collection destination
STATIC_ROOT = BASE_DIR / 'staticfiles'




# THE LABEL GROUP ROOT STATIC DIRECTORY FIX
# Include project-level static assets in Django's static-file collection.
_TLG_ROOT_STATIC = BASE_DIR / "static"
_TLG_STATIC_DIRS = list(globals().get("STATICFILES_DIRS", []))
if _TLG_ROOT_STATIC.is_dir() and _TLG_ROOT_STATIC not in _TLG_STATIC_DIRS:
    _TLG_STATIC_DIRS.append(_TLG_ROOT_STATIC)
STATICFILES_DIRS = _TLG_STATIC_DIRS