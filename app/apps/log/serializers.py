from apps.log.models import ActivityLog
from django.contrib.auth import get_user_model
from rest_framework import serializers, status
from rest_framework.exceptions import APIException

User = get_user_model()


class UnauthorizedError(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "인증 실패"
    default_code = "unauthorized"


class NopermissionError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "권한 없음"
    default_code = "forbidden"


class ActivityLogSerializer(serializers.ModelSerializer):
    """로그 조회용 시리얼라이저"""

    username = serializers.SerializerMethodField()
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "user_id",
            "username",
            "action",
            "action_display",
            "details",
            "created_at",
        ]

    def get_username(self, obj):
        if obj.user_id:
            return obj.user_id.nickname  # User 모델은 nickname 필드 사용
        return "Anonymous"
