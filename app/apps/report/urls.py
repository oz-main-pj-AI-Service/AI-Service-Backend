from apps.report import views
from django.urls import path

urlpatterns = [
    path(
        "api/reports", views.ReportListCreateView.as_view(), name="report-list-create"
    ),
    path(
        "api/reports/<uuid:id>", views.ReportDetailView.as_view(), name="report-detail"
    ),
]
