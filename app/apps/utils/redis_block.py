import os

import redis
from rest_framework import status
from rest_framework.exceptions import APIException

if os.getenv("DOCKER_ENV", "false").lower() == "true":
    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
else:
    REDIS_HOST = "localhost"

r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)


def get_login_attempt_key(key):
    return f"login_attempt_{key}"


class TooManyLoginAttempts(APIException):
    status_code = status.HTTP_403_FORBIDDEN

    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = "로그인 시도 횟수를 초과했습니다. 5분후에 다시 시도하세요."
        if code is None:
            code = "Too_much_attempts"
        self.detail = {"detail": detail, "code": code}


def check_login_attempt_key(key, limit=5, block_time=300):
    redis_key = get_login_attempt_key(key)
    attempts = r.get(redis_key)

    if attempts and int(attempts) >= limit:
        raise TooManyLoginAttempts()
    pipe = r.pipeline()
    pipe.incr(redis_key)
    pipe.expire(redis_key, block_time)
    pipe.execute()


def reset_login_attempt(key):
    redis_key = get_login_attempt_key(key)
    r.delete(redis_key)
