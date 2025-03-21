from django.apps import AppConfig

"""v1 = utils/signals.py에 있던 user관련 부분을 그냥 보기 쉽게 user에 다 옮겨놨습니다"""


class UserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.user"

    def ready(self):

        import logging

        from apps.log.models import ActivityLog
        from apps.utils.signals import activity_logged, get_client_ip
        from django.contrib.auth import get_user_model
        from django.contrib.auth.signals import user_logged_in, user_logged_out
        from django.db.models.signals import post_save
        from django.dispatch import receiver

        User = get_user_model()
        logger = logging.getLogger(__name__)

        # 1번 리시버
        # 1. 로그인 관련 핸들러
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

        # 2번 리시버
        # 2. 로그아웃 핸들러
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

        # 3번 리시버
        # 3. 로그인 시도 초기화 핸들러
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

        # 4번 리시버
        # 4. 사용자 계정 생성 로깅
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

        # 5번 리시버
        # 5. 이메일 인증 완료 로깅
        @receiver(post_save, sender=User)
        def log_email_verification(sender, instance, created, **kwargs):
            """이메일 인증 완료 시 로그 생성"""
            if (
                not created
                and hasattr(instance, "email_verified")
                and instance.email_verified
            ):
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

        # 6번 리시버
        # 6. 사용자 프로필 업데이트 로깅
        @receiver(post_save, sender=User)
        def log_profile_update(sender, instance, created, **kwargs):
            """사용자 프로필 업데이트 로깅"""
            # 계정 생성과 이메일 인증은 이미 별도 핸들러에서 처리
            if (
                not created
                and not getattr(instance, "_password_changed", False)
                and not (
                    hasattr(instance, "email_verified") and instance.email_verified
                )
            ):
                try:
                    ActivityLog.objects.create(
                        user_id=instance,
                        action=ActivityLog.ActionType.UPDATE_PROFILE,
                        ip_address="0.0.0.0",  # 요청 컨텍스트가 없어 기본값
                        user_agent="System",
                        details={
                            "message": "프로필 정보 업데이트",
                        },
                    )
                    logger.info(f"사용자 {instance.id} 프로필 업데이트 로그 기록")
                except Exception as e:
                    logger.error(f"프로필 업데이트 로깅 중 오류 발생: {e}")

        # 7번 리시버
        # 7. 사용자 비활성화/삭제 로깅
        @receiver(post_save, sender=User)
        def log_account_deactivation(sender, instance, **kwargs):
            """사용자 계정 비활성화/삭제 로깅"""
            # User 모델의 delete 메서드에서는 실제로 레코드를 삭제하지 않고
            # is_active를 False로, status를 DELETED로 변경
            if (
                not instance.is_active
                and instance.status == "DELETED"
                and instance.deleted_at
            ):
                try:
                    ActivityLog.objects.create(
                        user_id=instance,
                        action=ActivityLog.ActionType.UPDATE_PROFILE,
                        ip_address="0.0.0.0",
                        user_agent="System",
                        details={
                            "message": "계정 삭제",
                        },
                    )
                    logger.info(f"사용자 {instance.id} 계정 삭제 로그 기록")
                except Exception as e:
                    logger.error(f"계정 삭제 로깅 중 오류 발생: {e}")
            # 계정이 비활성화된 경우 (삭제는 아님)
            elif not instance.is_active and instance.status == "SUSPENDED":
                try:
                    ActivityLog.objects.create(
                        user_id=instance,
                        action=ActivityLog.ActionType.UPDATE_PROFILE,
                        ip_address="0.0.0.0",
                        user_agent="System",
                        details={
                            "message": "계정 비활성화",
                        },
                    )
                    logger.info(f"사용자 {instance.id} 계정 비활성화 로그 기록")
                except Exception as e:
                    logger.error(f"계정 비활성화 로깅 중 오류 발생: {e}")

        # 8번 리시버
        # 8. 패스워드 변경 로깅 (Django 시그널 사용)
        try:
            from django.contrib.auth.signals import user_password_changed

            @receiver(user_password_changed)
            def log_password_change(sender, request, user, **kwargs):
                """비밀번호 변경 로깅"""
                try:
                    # 요청 컨텍스트가 있을 경우 IP와 User-Agent 정보 사용
                    ip_address = "0.0.0.0"
                    user_agent = "System"

                    if request:
                        from apps.utils.signals import get_client_ip

                        ip_address = get_client_ip(request)
                        user_agent = request.META.get("HTTP_USER_AGENT", "")

                    # 비밀번호 변경 플래그 설정 (프로필 업데이트와 중복 로깅 방지)
                    user._password_changed = True

                    ActivityLog.objects.create(
                        user_id=user,
                        action=ActivityLog.ActionType.UPDATE_PROFILE,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        details={
                            "message": "비밀번호 변경",
                        },
                    )
                    logger.info(f"사용자 {user.id} 비밀번호 변경 로그 기록")
                except Exception as e:
                    logger.error(f"비밀번호 변경 로깅 중 오류 발생: {e}")

        except ImportError:
            # Django 버전에 따라 user_password_changed 시그널이 없을 수 있음
            logger.warning("user_password_changed 시그널을 사용할 수 없습니다.")
