from apps.report.models import Report
from rest_framework import serializers


class ReportListCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Report
        fields = [
            "id",
            "user_id",
            "title",
            "description",
            "status",
            "type",
            "admin_comment",
            "admin_id",
            "created_at",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "user_id": {"read_only": True},
            "admin_comment": {"required": False},
            "admin_id": {"required": False},
            "created_at": {"read_only": True},
        }

    def validate_title(self, value):
        if len(value) > 100:
            raise serializers.ValidationError(
                detail="제목은 100자 이내로 작성해주세요", code="title_too_long"
            )
        return value


class ReportRetrieveUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            "id",
            "user_id",
            "title",
            "description",
            "status",
            "type",
            "admin_comment",
            "admin_id",
            "created_at",
        ]
        extra_kwargs = {
            "user_id": {"read_only": True},
            "id": {"read_only": True},
            "admin_comment": {"required": False, "read_only": True},
            "admin_id": {"required": False, "read_only": True},
            "created_at": {"read_only": True},
        }


class AdminReportUpdateSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    user_id = serializers.SerializerMethodField()
    admin_id = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = "__all__"

    def get_user_id(self, obj):
        return str(obj.user_id.id) if obj.user_id else None

    def get_admin_id(self, obj):
        return str(obj.admin_id.id) if obj.admin_id else None
