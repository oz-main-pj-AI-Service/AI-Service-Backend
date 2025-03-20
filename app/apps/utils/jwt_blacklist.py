import redis
from django.conf import settings

redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST, port=6379, db=2, decode_responses=True
)


def add_to_blacklist(token, expires_in):
    """Redis에 블랙리스트 추가"""
    redis_client.setex(f"blacklist:{token}", expires_in, "blacklisted")


def is_blacklisted(token):
    """JWT가 블랙리스트에 있는지 확인"""
    return redis_client.get(token) is not None
