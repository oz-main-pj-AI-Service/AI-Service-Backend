from apps.utils.jwt_blacklist import is_blacklisted
from rest_framework.exceptions import AuthenticationFailed
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
