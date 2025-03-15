from django.urls.conf import include, path

urlpatterns = [
    path("api/user/", include("apps.user.urls")),
]
