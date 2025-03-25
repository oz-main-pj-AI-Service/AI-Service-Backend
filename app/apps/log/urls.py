from apps.log.views import LogListCreateView, LogRetrieveAPIView
from django.urls.conf import path

app_name = "log"

urlpatterns = [
    path("", LogListCreateView.as_view(), name="list-create"),
    path("<uuid:pk>/", LogRetrieveAPIView.as_view(), name="retrieve"),
    path("admin/", LogListCreateView.as_view(), name="admin-list-create"),
    path(
        "admin/<uuid:log_id>/",
        LogListCreateView.as_view(),
        name="admin-log-list-create",
    ),
]
