import uuid

from django.conf import settings
from django.db import models


class Report(models.Model):
    class StatusType(models.TextChoices):
        OPEN = "OPEN", "접수됨"
        IN_PROGRESS = "IN_PROGRESS", "처리중"
        RESOLVED = "RESOLVED", "해결됨"
        CLOSED = "CLOSED", "종료됨"

    class ReportType(models.TextChoices):
        ERROR = "ERROR", "오류"
        QUESTION = "QUESTION", "질문"
        FEATURE_REQUEST = "FEATURE_REQUEST", "기능 요청"
        OTHER = "OTHER", "기타"

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, help_text="Report ID"
    )
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports",
        help_text="사용자 ID",
    )
    title = models.CharField(max_length=100, help_text="요청 제목")
    description = models.TextField(help_text="상세 오류")
    status = models.CharField(
        max_length=20,
        choices=StatusType.choices,
        default=StatusType.OPEN,
        help_text="진행 상태(OPEN, IN_PROGRESS, RESOLVED, CLOSED)",
    )
    type = models.CharField(
        max_length=20,
        choices=ReportType.choices,
        help_text="요청 타입(ERROR, QUESTION, FEATURE_REQUEST, OTHER)",
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성일")
    admin_comment = models.TextField(null=True, blank=True, help_text="관리자 답변")
    admin_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handled_reports",
        help_text="관리자 ID",
    )

    # 테이블명, 정렬순서, 인덱스 설정
    class Meta:
        db_table = "report"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.type}) - {self.status}"

    # Report 모델을 딕셔너리 형태로 변환
    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id.id),
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "type": self.type,
            "created_at": self.created_at.isoformat(),
            # 관리자 정보가 없을 경우 None으로 반환 = 관리자 추가단
            "admin_comment": self.admin_comment,
            "admin_id": str(self.admin_id.id) if self.admin_id else None,
        }
