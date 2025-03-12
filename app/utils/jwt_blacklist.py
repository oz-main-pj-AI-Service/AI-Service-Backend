import redis
from django.conf import settings

redis_client = redis.StrictRedis(host="127.0.0.1", port=6379, db=2, decode_responses=True)

def add_to_blacklist(token):
    """JWT를 Redis 블랙리스트에 추가"""
    redis_client.set(token, "blacklisted", ex=3600)  # 1시간 후 만료

def is_blacklisted(token):
    """JWT가 블랙리스트에 있는지 확인"""
    return redis_client.get(token) is not None