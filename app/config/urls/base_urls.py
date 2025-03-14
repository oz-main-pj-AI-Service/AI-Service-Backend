from django.urls import include
from django.urls.conf import path

urlpatterns = [path("api/ai/", include("apps.ai.urls"))]
