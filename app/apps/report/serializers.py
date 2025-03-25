from apps.report.models import Report
from rest_framework import serializers


class ReportListCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Report
        fields = [
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
            "admin_comment": {"required": False},
            "admin_id": {"required": False},
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
