import redis
from django.conf import settings

from .jwt_blacklist import redis_client

redis_client = redis.StrictRedis(
    host="127.0.0.1", port=6379, db=1, decode_responses=True
)


def cache_jwt(user_id, token, expiry=1800):
    """
    JWT를 Redis에 저장 (기본 만료시간: 30분)
    """
    redis_client.set(f"jwt:{user_id}", token, ex=expiry)


def get_cached_jwt(user_id):
    """
    Redis에서 JWT 가져오기
    """
    return redis_client.get(f"jwt:{user_id}")

def remove_cached_jwt(user_id):
    """
    Redis에서 JWT 삭제 (로그아웃 시)
    """
    redis_client.delete(f"jwt:{user_id}")