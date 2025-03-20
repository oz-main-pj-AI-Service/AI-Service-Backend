import uuid

from django.conf import settings
from django.db import models


class ActivityLog(models.Model):
    class ActionType(models.TextChoices):
        LOGIN = "LOGIN", "로그인"
        LOGOUT = "LOGOUT", "로그아웃"
        UPDATE_PROFILE = "UPDATE_PROFILE", "프로필 업데이트"
        VIEW_REPORT = "VIEW_REPORT", "리포트 조회"

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, help_text="로그 ID"
    )
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="사용자 ID(NULL가능)",
    )
    action = models.CharField(
        max_length=255, choices=ActionType.choices, help_text="로그액션"
    )
    ip_address = models.GenericIPAddressField(
        protocol="both", unpack_ipv4=True, help_text="사용자 IP"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성일")
    details = models.JSONField(null=True, blank=True, help_text="추가 정보")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user_id"]),
            models.Index(fields=["action"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["ip_address"]),
        ]

    def __str__(self):
        user_info = f"User {self.user_id}" if self.user_id else "Anonymous"
        return f"{self.action} by {user_info} at {self.created_at}"

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id.id) if self.user_id else None,
            "action": self.action,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
            "details": self.details or {},
        }

    # 특정 사용자 총 로그 수
    @classmethod
    def get_user_log_count(cls, user_id):
        return cls.objects.filter(user_id=user_id).count()
