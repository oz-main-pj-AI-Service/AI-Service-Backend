from apps.report import views
from django.urls import path

app_name = "report"
urlpatterns = [
    path("", views.ReportListCreateView.as_view(), name="list-create"),
    path(
        "<uuid:pk>/",
        views.ReportDetailUpdateDestroyView.as_view(),
        name="detail-update-destroy",
    ),
    path(
        "<uuid:pk>/admin/",
        views.AdminReportUpdateView.as_view(),
        name="admin-update",
    ),
]
