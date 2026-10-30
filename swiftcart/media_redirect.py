from urllib.parse import quote

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseNotFound


class ProductMediaStaticRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info or ""
        prefix = "/media/products/"

        if path.startswith(prefix):
            relative_path = path[len(prefix):]
            parts = relative_path.split("/")

            if (
                not relative_path
                or any(part in ("", ".", "..") for part in parts)
                or "\\" in relative_path
                or "\x00" in relative_path
            ):
                return HttpResponseNotFound("Product image not found.")

            destination = (
                settings.STATIC_URL.rstrip("/")
                + "/products/"
                + quote(relative_path, safe="/")
            )

            return HttpResponseRedirect(destination)

        return self.get_response(request)
