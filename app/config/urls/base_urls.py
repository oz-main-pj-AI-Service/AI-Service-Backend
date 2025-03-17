from django.urls.conf import include, path

urlpatterns = [
    path("api/user/", include("apps.user.urls")),
    path("api/reports/", include("apps.report.urls")),
    path("api/ai/", include("apps.ai.urls")),
]
