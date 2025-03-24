from apps.utils.jwt_blacklist import is_blacklisted
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


class RedisJWTAuthentication(JWTAuthentication):
    """JWT를 Redis 기반으로 블랙리스트 검증하는 커스텀 인증 클래스"""

    def authenticate(self, request):
        auth_result = super().authenticate(request)
        if not auth_result:
            return None

        user, token = auth_result

        # ✅ 블랙리스트 검증
        if is_blacklisted(str(token)):
            raise AuthenticationFailed("로그아웃된 토큰입니다.")

        return user, token


class IsAuthenticatedJWTAuthentication(IsAuthenticated):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated(
                detail="인증되지 않은 사용자입니다.", code="unauthorized"
            )

        # 예시: 추가로 특정 권한이 없는 경우
        if not request.user.is_active:
            raise PermissionDenied(detail="접근 권한이 없습니다.", code="forbidden")

        return True
