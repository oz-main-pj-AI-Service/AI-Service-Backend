# Generated by Django 5.1.7 on 2025-03-18 07:51

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Report",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Report ID",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("title", models.CharField(help_text="요청 제목", max_length=100)),
                ("description", models.TextField(help_text="상세 오류")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("OPEN", "접수됨"),
                            ("IN_PROGRESS", "처리중"),
                            ("RESOLVED", "해결됨"),
                            ("CLOSED", "종료됨"),
                        ],
                        default="OPEN",
                        help_text="진행 상태(OPEN, IN_PROGRESS, RESOLVED, CLOSED)",
                        max_length=20,
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("ERROR", "오류"),
                            ("QUESTION", "질문"),
                            ("FEATURE_REQUEST", "기능 요청"),
                            ("OTHER", "기타"),
                        ],
                        help_text="요청 타입(ERROR, QUESTION, FEATURE_REQUEST, OTHER)",
                        max_length=20,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, help_text="생성일"),
                ),
                (
                    "admin_comment",
                    models.TextField(blank=True, help_text="관리자 답변", null=True),
                ),
                (
                    "admin_id",
                    models.ForeignKey(
                        blank=True,
                        help_text="관리자 ID",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="handled_reports",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user_id",
                    models.ForeignKey(
                        help_text="사용자 ID",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reports",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "report",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["user_id"], name="report_user_id_ef95fe_idx"),
                    models.Index(fields=["status"], name="report_status_74972f_idx"),
                    models.Index(fields=["type"], name="report_type_9eba38_idx"),
                    models.Index(
                        fields=["created_at"], name="report_created_2a12c2_idx"
                    ),
                ],
            },
        ),
    ]
