from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve

admin.site.site_header = "Eventora administration"
admin.site.site_title = "Eventora admin"
admin.site.index_title = "Manage events, bookings and users"

urlpatterns = [
    # Browsers (and the admin, which has no <link rel="icon">) request /favicon.ico.
    path("favicon.ico", RedirectView.as_view(url=f"/{settings.STATIC_URL.strip('/')}/img/favicon.svg", permanent=True)),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("bookings/", include("bookings.urls")),
    path("", include("events.urls")),
]

# Serve uploaded banners. Fine for a demo deployment; use object storage at scale.
if settings.DEBUG or settings.SERVE_MEDIA:
    urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]
