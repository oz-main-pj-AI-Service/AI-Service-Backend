# Generated by Django 5.1.7 on 2025-03-13 07:24

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ActivityLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="로그 ID",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("LOGIN", "로그인"),
                            ("LOGOUT", "로그아웃"),
                            ("UPDATE_PROFILE", "프로필 업데이트"),
                            ("VIEW_REPORT", "리포트 조회"),
                        ],
                        help_text="로그액션",
                        max_length=255,
                    ),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(
                        help_text="사용자 IP", unpack_ipv4=True
                    ),
                ),
                ("user_agent", models.TextField(help_text="사용자 브라우저 정보")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, help_text="생성일"),
                ),
                (
                    "details",
                    models.JSONField(blank=True, help_text="추가 정보", null=True),
                ),
                (
                    "user_id",
                    models.ForeignKey(
                        blank=True,
                        help_text="사용자 ID(NULL가능)",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "activity_log",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["user_id"], name="activity_lo_user_id_f9e1c8_idx"
                    ),
                    models.Index(
                        fields=["action"], name="activity_lo_action_f14761_idx"
                    ),
                    models.Index(
                        fields=["created_at"], name="activity_lo_created_8906e2_idx"
                    ),
                    models.Index(
                        fields=["ip_address"], name="activity_lo_ip_addr_866d60_idx"
                    ),
                ],
            },
        ),
    ]
