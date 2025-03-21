from django.apps import AppConfig


class ReportConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.report"

    def ready(self):

        import logging

        import apps.utils.signals
        from apps.log.models import ActivityLog
        from apps.report.models import Report
        from django.db.models.signals import post_delete, post_save
        from django.dispatch import receiver

        logger = logging.getLogger(__name__)

        # 1번째 리시버 생성 수정 (삭제는 넣지 않음) = 우리 삭제기능 없어서 안 넣었습니다
        @receiver(post_save, sender=Report)
        def log_report(sender, instance, created, **kwargs):
            """문의내역 로깅 = 문의 남길 시 로그 기록"""
            action_msg = "문의내역 생성" if created else "문의내역 수정"
            try:
                ActivityLog.objects.create(
                    user_id=instance.user_id,
                    action=ActivityLog.ActionType.REPORT,
                    ip_address="0.0.0.0",
                    user_agent="System",
                    details={
                        "message": action_msg,
                        "report_id": str(instance.id),
                        "report_title": instance.title,
                    },
                )
                logger.info(f"{action_msg} 로그 기록: {instance.id}")
            except Exception as e:
                logger.error(f"레포트 활동 로깅 중 오류 발생: {e}")
