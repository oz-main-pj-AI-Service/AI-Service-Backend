from apps.report import views
from django.urls import path

urlpatterns = [
    path("", views.ReportListCreateView.as_view(), name="report-list-create"),
    path("<uuid:id>/", views.ReportDetailView.as_view(), name="report-detail"),
]
