import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


# ai 요청 정보 저장 모델
class AiRequest(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, help_text="AI 요청 ID"
    )
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, help_text="사용자 ID"
    )
    request_type = models.CharField(max_length=255, help_text="AI 요청 타입")
    request_data = models.JSONField(help_text="요청 데이터")
    response_data = models.JSONField(null=True, blank=True, help_text="응답 데이터")
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성일")

    class Meta:
        db_table = "ai_request"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.request_type} - {self.created_at}"
