import logging

import django.dispatch
from apps.log.models import ActivityLog
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()
logger = logging.getLogger(__name__)

# 사용자 커스텀 시그널 정의
activity_logged = django.dispatch.Signal()

"""아까 처음에 추가한 get_client_ip 함수부터 views단에 들어있는 receiver함수들을 여기로 옮겼습니다"""


def get_client_ip(request):
    """클라이언트의 IP 주소를 획득하는 유틸리티 함수"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


"""아래부터 리시버 시그널 함수"""


@receiver(user_logged_in)
def log_user_login(sender, user, request, **kwargs):
    """사용자 로그인 시 activity log 기록"""
    try:
        log = ActivityLog.objects.create(
            user_id=user,
            action=ActivityLog.ActionType.LOGIN,
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            details={"message": "로그인 성공"},
        )
        logger.info(f"사용자 {user.id} 로그인 성공")

        # 로그인 성공 시 activity_logged 시그널 발생
        activity_logged.send(
            sender=ActivityLog,
            user=user,
            action=ActivityLog.ActionType.LOGIN,
            log_instance=log,
        )
    except Exception as e:
        logger.error(f"사용자 로그인 로깅 중 오류 발생: {e}")


@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    """사용자 계정 생성 시 로그 자동 기록"""
    if created:
        try:
            ActivityLog.objects.create(
                user_id=instance,
                action=ActivityLog.ActionType.UPDATE_PROFILE,
                ip_address="0.0.0.0",  # 시스템 액션으로 기본값 설정
                user_agent="System",
                details={"message": "사용자 계정 생성"},
            )
            logger.info(f"사용자 {instance.id} 계정 생성 로그 기록")
        except Exception as e:
            logger.error(f"사용자 계정 생성 로깅 중 오류 발생: {e}")


@receiver(user_logged_out)
def log_user_logout(sender, user, request, **kwargs):
    """사용자 로그아웃 시 ActivityLog 생성"""
    if user:
        try:
            ActivityLog.objects.create(
                user_id=user,
                action=ActivityLog.ActionType.LOGOUT,
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                details={"message": "로그아웃 성공"},
            )
            logger.info(f"사용자 {user.id} 로그아웃 성공")
        except Exception as e:
            logger.error(f"사용자 로그아웃 로깅 중 오류 발생: {e}")


@receiver(activity_logged)
def handle_activity_log(sender, user, action, log_instance, **kwargs):
    """로그인 성공 시 로그인 시도 횟수 초기화"""
    if action == ActivityLog.ActionType.LOGIN:
        if user.is_authenticated:
            try:
                # 로그인 시도 횟수 리셋
                user.login_attempts = 0
                user.save(update_fields=["login_attempts"])
                logger.info(f"사용자 {user.id} 로그인 시도 횟수 초기화")
            except Exception as e:
                logger.error(f"로그인 시도 횟수 초기화 중 오류 발생: {e}")


@receiver(activity_logged)
def create_login_log(sender, user, action, log_instance, **kwargs):
    """JWT 인증 시 추가 처리 로직"""
    # 로그인 시 처리할 수 있는 추가 작업
    pass


@receiver(post_save, sender=User)
def log_email_verification(sender, instance, created, **kwargs):
    """이메일 인증 완료 시 로그 생성"""
    if not created and hasattr(instance, "email_verified") and instance.email_verified:
        try:
            ActivityLog.objects.create(
                user_id=instance,
                action=ActivityLog.ActionType.UPDATE_PROFILE,
                ip_address="0.0.0.0",
                user_agent="System",
                details={"message": "이메일 인증 완료"},
            )
            logger.info(f"사용자 {instance.id} 이메일 인증 완료 로그 기록")
        except Exception as e:
            logger.error(f"이메일 인증 완료 로깅 중 오류 발생: {e}")
