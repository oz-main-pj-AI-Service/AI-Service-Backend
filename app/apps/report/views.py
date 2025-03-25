from apps.log.models import ActivityLog
from apps.log.views import get_client_ip
from apps.report.models import Report
from apps.report.serializers import (
    ReportListCreateSerializer,
    ReportRetrieveSerializer,
    ReportUpdateSerializer,
)
from apps.utils.authentication import IsAuthenticatedJWTAuthentication
from apps.utils.pagination import Pagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveDestroyAPIView,
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
)
from rest_framework.response import Response


class ReportListCreateView(ListCreateAPIView):
    """리포트 목록 조회 및 생성 API"""

    queryset = Report.objects.all()
    permission_classes = [IsAuthenticatedJWTAuthentication]
    pagination_class = Pagination
    serializer_class = ReportListCreateSerializer

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={
            200: "msg:조회 성공",
            401: openapi.Response(
                description="- `code`:`unauthorized`, 인증되지 않은 사용자입니다\n"
            ),
            403: openapi.Response(
                description=("- `code`:`forbidden`, 관리자가 아닙니다.\n")
            ),
        },
    )
    def get(self, request):
        """스웨거용 get"""

        ActivityLog.objects.create(
            user_id=self.request.user,
            action="VIEW_REPORT",
            ip_address=get_client_ip(self.request),
        )

        return super().get(request)

    def get_queryset(self):
        queryset = super().get_queryset()

        if not self.request.user.is_superuser:
            queryset = queryset.filter(user_id=self.request.user.id)

        # 필터링
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        report_type = self.request.query_params.get("type")
        if report_type:
            queryset = queryset.filter(report_type=report_type)

        return queryset

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=ReportListCreateSerializer,
        responses={
            201: "msg:리포트 생성 완료.",
            400: openapi.Response(
                description=(
                    "프론트 분들이 필수 필드 title, description는 입력하게 만들어놔 주세요\n"
                    "admin_comnet, admin_id는 생성시에는 만들어지지 않습니다. 넣는 입력칸 안만드셔도 되여\n"
                    "잘못된 요청 코드 \n"
                    "- `code`:`title_too_long`, 제목이 100자 이상"
                )
            ),
            401: openapi.Response(
                description="- `code`:`unauthorized`, 인증되지 않은 사용자입니다\n"
            ),
            403: openapi.Response(
                description=("- `code`:`forbidden`, 관리자가 아닙니다.\n")
            ),
        },
    )
    def create(self, request, *args, **kwargs):
        """스웨거용 create"""
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user)
        ActivityLog.objects.create(
            user_id=self.request.user,
            action="CREATE_REPORT",
            ip_address=get_client_ip(self.request),
            details={
                "title": self.request.data.get("title"),
                "description": self.request.data.get("description"),
            },
        )


class ReportDetailView(RetrieveDestroyAPIView):
    """리포트 상세 조회, 수정, 삭제 API"""

    queryset = Report.objects.all()
    serializer_class = ReportRetrieveSerializer
    permission_classes = [IsAuthenticatedJWTAuthentication]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={
            200: "msg:리포트 조회.",
            400: openapi.Response(
                description=(
                    "잘못된 요청 코드 \n" "- `code`:`not_found`, 리포트를 찾지 못함."
                )
            ),
            401: openapi.Response(
                description="- `code`:`unauthorized`, 인증되지 않은 사용자입니다\n"
            ),
            403: openapi.Response(
                description=("- `code`:`not_Admin`, 관리자가 아닙니다.\n")
            ),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        ActivityLog.objects.create(
            user_id=self.request.user,
            action="VIEW_REPORT",
            ip_address=get_client_ip(self.request),
        )
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={
            200: "msg:리포트 조회.",
            400: openapi.Response(
                description=(
                    "잘못된 요청 코드 \n" "- `code`:`not_found`, 리포트를 찾지 못함."
                )
            ),
            401: openapi.Response(
                description="- `code`:`unauthorized`, 인증되지 않은 사용자입니다\n"
            ),
            403: openapi.Response(
                description=(
                    "- `code`:`not_Admin`, 관리자가 아닙니다.\n"
                    "- `code`:`not_Author`, 작성자가 아닙니다.\n"
                )
            ),
        },
    )
    def delete(self, request, *args, **kwargs):
        """리포트 삭제"""
        report = self.get_object()
        if report.user_id != self.request.user.id:
            raise PermissionDenied(detail="작성자가 아닙니다.", code="not_Author")
        ActivityLog.objects.create(
            user_id=self.request.user,
            action="DELETE_REPORT",
            ip_address=get_client_ip(self.request),
        )
        return super().delete(request, *args, **kwargs)


class ReportUpdateView(UpdateAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportUpdateSerializer
    permission_classes = [IsAuthenticatedJWTAuthentication]

    def get_object(self):
        response = super().get_object()
        if not response.user_id == self.request.user.id:
            raise PermissionDenied(
                detail="사용자의 리포트가 아닙니다.", code="not_Author"
            )
        return response

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=ReportUpdateSerializer,
        responses={
            200: "msg:리포트 조회.",
            400: openapi.Response(
                description=(
                    "잘못된 요청 코드 \n" "- `code`:`not_found`, 리포트를 찾지 못함."
                )
            ),
            401: openapi.Response(
                description="- `code`:`unauthorized`, 인증되지 않은 사용자입니다\n"
            ),
            403: openapi.Response(
                description=("- `code`:`not_Admin`, 관리자가 아닙니다.\n")
            ),
        },
    )
    def update(self, request, *args, **kwargs):
        ActivityLog.objects.create(
            user_id=self.request.user,
            action="UPDATE_REPORT",
            ip_address=get_client_ip(self.request),
            details={
                "title": self.request.data.get("title"),
                "description": self.request.data.get("description"),
            },
        )
        return super().update(request, *args, **kwargs)


class AdminReportUpdateView(UpdateAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportUpdateSerializer
    permission_classes = [IsAuthenticatedJWTAuthentication]

    def perform_update(self, serializer):
        if not self.request.user.is_superuser:
            raise PermissionDenied(detail="관리자가 아닙니다.", code="not_Admin")
        serializer.save(admin_id=self.request.user)
        ActivityLog.objects.create(
            user_id=self.request.user,
            action="UPDATE_REPORT",
            ip_address=get_client_ip(self.request),
            details={
                "admin_comment": self.request.data.get("admin_comment"),
                "admin_id": self.request.user.id,
            },
        )

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=ReportUpdateSerializer,
        responses={
            200: "msg:업데이트 성공.",
            400: openapi.Response(
                description=(
                    "잘못된 요청 코드 \n" "- `code`:`not_found`, 리포트를 찾지 못함."
                )
            ),
            401: openapi.Response(
                description="- `code`:`unauthorized`, 인증되지 않은 사용자입니다\n"
            ),
            403: openapi.Response(
                description=("- `code`:`not_Admin`, 관리자가 아닙니다.\n")
            ),
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
