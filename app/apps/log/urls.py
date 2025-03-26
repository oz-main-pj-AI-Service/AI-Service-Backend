from apps.log.views import LogListView, LogRetrieveAPIView
from django.urls.conf import path

app_name = "log"

urlpatterns = [
    path("", LogListView.as_view(), name="list-create"),
    path("<uuid:log_id>/", LogRetrieveAPIView.as_view(), name="retrieve"),
]
