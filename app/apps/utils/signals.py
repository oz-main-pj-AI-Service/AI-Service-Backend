import logging

import django.dispatch
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)

# 사용자 커스텀 시그널 정의
activity_logged = django.dispatch.Signal()

"""v1 = 아까 처음에 추가한 get_client_ip 함수부터 views단에 들어있는 receiver함수들을 여기로 옮겼습니다"""
"""v2 = get_client_ip 함수 외에 로그인 함수는 user/apps부분으로 옮겼어요 """


def get_client_ip(request):
    """클라이언트의 IP 주소를 획득하는 유틸리티 함수"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
