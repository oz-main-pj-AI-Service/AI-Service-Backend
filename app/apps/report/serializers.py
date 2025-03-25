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


class ReportRetrieveSerializer(serializers.ModelSerializer):
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
        ]
        extra_kwargs = {
            "user_id": {"read_only": True},
            "id": {"read_only": True},
            "created_at": {"read_only": True},
        }


class ReportUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["user_id", "title", "description", "status", "type"]
        extra_kwargs = {
            "user_id": {"read_only": True},
            "admin_comment": {"required": False},
            "admin_id": {"required": False},
        }


class AdminReportUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["status", "admin_comment"]
