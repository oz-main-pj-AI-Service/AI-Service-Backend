from django.http import JsonResponse
from django.urls.conf import include, path


def health_check(request):
    return JsonResponse({"status": "ok"}, status=200)


urlpatterns = [
    path("api/user/", include("apps.user.urls")),
    path("api/reports/", include("apps.report.urls")),
    path("api/ai/", include("apps.ai.urls")),
    path("api/logs/", include("apps.log.urls")),
    path("api/healthz/", health_check),
]
