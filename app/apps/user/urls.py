from apps.user.social_view import GoogleSocialLoginCallbackView, GoogleSocialLoginView
from apps.user.views import (
    AdminUserListView,
    AdminUserUpdateView,
    ChangePasswordView,
    FindEmail,
    UserLoginView,
    UserLogoutView,
    UserProfileView,
    UserRegisterView,
    VerifyEmailView,
)
from django.urls.conf import include, path

app_name = "user"

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("profile/change-pw/", ChangePasswordView.as_view(), name="change-pw"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    # 소셜로그인
    path("social-login/google/", GoogleSocialLoginView.as_view(), name="google-login"),
    path(
        "social-login/google/callback/",
        GoogleSocialLoginCallbackView.as_view(),
        name="google-login-callback",
    ),
    path("social-login/naver/", GoogleSocialLoginView.as_view(), name="naver-login"),
    path(
        "social-login/naver/callback/",
        GoogleSocialLoginCallbackView.as_view(),
        name="naver-login-callback",
    ),
    # 비밀번호 찾기
    path("find-email/", FindEmail.as_view(), name="find-email"),
    # admin
    path("admin/", AdminUserListView.as_view(), name="admin-users-list"),
    path(
        "admin/<uuid:user_id>", AdminUserUpdateView.as_view(), name="admin-user-update"
    ),
]
