from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .jwt_cache import get_cached_jwt

class RedisJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        auth_result = super().authenticate(request)
        if auth_result is None:
            return None

        user, token = auth_result

        # Redis에서 JWT 가져오기
        cached_token = get_cached_jwt(user.id)
        if cached_token != str(token):
            raise AuthenticationFailed("Invalid or expired token.")

        return user, token