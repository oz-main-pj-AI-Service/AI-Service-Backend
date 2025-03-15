from django.urls.conf import include, path

urlpatterns = [
    path("", include("apps.report.urls")),
]
