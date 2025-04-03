from apps.user.social_view import (
    GoogleSocialLoginCallbackView,
    NaverSocialLoginCallbackView,
)
from apps.user.views import (
    AdminUserListView,
    AdminUserUpdateView,
    ChangePasswordNoLoginView,
    ChangePasswordView,
    CheckEmailDuplicate,
    FindEmail,
    FindPasswordView,
    RefreshTokenView,
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
    path("check-email/", CheckEmailDuplicate.as_view(), name="check-email"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("refresh-token/", RefreshTokenView.as_view(), name="refresh-token"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("profile/change-pw/", ChangePasswordView.as_view(), name="change-pw"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    # 소셜로그인
    # path("social-login/google/", GoogleSocialLoginView.as_view(), name="google-login"),
    path(
        "social-login/google/callback/",
        GoogleSocialLoginCallbackView.as_view(),
        name="google-login-callback",
    ),
    # path("social-login/naver/", NaverSocialLoginView.as_view(), name="naver-login"),
    path(
        "social-login/naver/callback/",
        NaverSocialLoginCallbackView.as_view(),
        name="naver-login-callback",
    ),
    # 비밀번호 찾기
    path("find-email/", FindEmail.as_view(), name="find-email"),
    path("find-password/", FindPasswordView.as_view(), name="find-password"),
    path("change-pw/", ChangePasswordNoLoginView.as_view(), name="change-pw-not-login"),
    # admin
    path("admin/", AdminUserListView.as_view(), name="admin-users-list"),
    path("admin/<uuid:pk>", AdminUserUpdateView.as_view(), name="admin-user-update"),
]
