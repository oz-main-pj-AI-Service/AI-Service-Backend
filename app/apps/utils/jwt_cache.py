import json

import redis
from django.conf import settings

# Redis 연결 설정
redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True
)


def store_access_token(user_id, access_token, expires_in):
    """Redis에 Access Token 저장"""
    redis_client.setex(f"user:{user_id}:access_token", expires_in, access_token)


def get_access_token(user_id):
    """Redis에서 Access Token 가져오기"""
    return redis_client.get(f"user:{user_id}:access_token")


def delete_access_token(user_id):
    """Redis에서 Access Token 삭제 (로그아웃 시)"""
    redis_client.delete(f"user:{user_id}:access_token")
