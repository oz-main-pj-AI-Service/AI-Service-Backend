from apps.report import views
from django.urls import path

app_name = "report"
urlpatterns = [
    path("", views.ReportListCreateView.as_view(), name="report-list-create"),
    path("<uuid:report_id>/", views.ReportDetailView.as_view(), name="report-detail"),
    path(
        "<uuid:report_id>/admin/",
        views.AdminReportUpdateView.as_view(),
        name="admin-report-update",
    ),
]
