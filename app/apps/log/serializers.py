from apps.log.models import ActivityLog
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


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


class ActivityLogCreateSerializer(serializers.ModelSerializer):
    """로그 생성용 시리얼라이저"""

    class Meta:
        model = ActivityLog
        fields = ["action", "details"]

    def validate_action(self, value):
        """액션 유효성 검사"""
        valid_actions = [choice[0] for choice in ActivityLog.ActionType.choices]
        if value not in valid_actions:
            raise serializers.ValidationError(
                f"유효하지 않은 액션: {value}. 유효한 액션: {', '.join(valid_actions)}"
            )
        return value


class UserActivityLogSerializer(serializers.ModelSerializer):
    """사용자 활동 로그 요약 시리얼라이저"""

    log_count = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "nickname", "email", "log_count", "last_login"]

    def get_log_count(self, obj):
        return ActivityLog.get_user_log_count(obj.id)

    def get_last_login(self, obj):
        last_login_log = (
            ActivityLog.objects.filter(
                user_id=obj.id, action=ActivityLog.ActionType.LOGIN
            )
            .order_by("-created_at")
            .first()
        )

        if last_login_log:
            return {
                "timestamp": last_login_log.created_at.isoformat(),
                "ip_address": last_login_log.ip_address,
            }
        return None
