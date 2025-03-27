from django.conf import settings
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]

from .base_urls import urlpatterns as base_urls
from .local_url import urlpatterns as local_urls

urlpatterns += base_urls

if settings.DEBUG:
    urlpatterns += local_urls
