from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


from django.conf import settings as django_settings
from django.urls import re_path as django_re_path
from django.views.static import serve as django_serve
urlpatterns = [
    django_re_path(
        r"^media/(?P<path>.*)$",
        django_serve,
        {"document_root": django_settings.MEDIA_ROOT},
    ),


    path('company-orders/', include('company_orders.urls')),
    path("admin/", admin.site.urls),
    path("staff/", include("staff.urls")),
    path("", include("products.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
