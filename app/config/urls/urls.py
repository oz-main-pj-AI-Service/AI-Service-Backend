from django.conf import settings
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    from .local_url import urlpatterns as local_urls

    urlpatterns += local_urls

from .base_urls import urlpatterns as base_urls

urlpatterns += base_urls
