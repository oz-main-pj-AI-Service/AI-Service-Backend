from apps.log.views import LogListCreateView
from django.urls.conf import path

app_name = "log"

urlpatterns = [
    path("", LogListCreateView.as_view(), name="log-list-create"),
    path("<uuid:log_id>/", LogListCreateView.as_view(), name="log-list-create"),
    path("admin/", LogListCreateView.as_view(), name="admin-log-list-create"),
    path(
        "admin/<uuid:log_id>/",
        LogListCreateView.as_view(),
        name="admin-log-list-create",
    ),
]
