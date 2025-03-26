from apps.log.models import ActivityLog
from apps.log.serializers import ActivityLogSerializer
from apps.utils.authentication import IsAuthenticatedJWTAuthentication
from apps.utils.pagination import Pagination
from django.contrib.auth import get_user_model
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework.generics import ListAPIView, RetrieveAPIView

User = get_user_model()


# 활동 로그 조회 및 생성 API
class LogListView(ListAPIView):
    queryset = ActivityLog.objects.all()
    pagination_class = Pagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["action", "ip_address"]
    ordering_fields = ["created_at", "action"]
    permission_classes = [IsAuthenticatedJWTAuthentication]
    serializer_class = ActivityLogSerializer

    @swagger_auto_schema(
        security=[{"Bearer": []}],  # 토큰 인증
        responses={
            200: ActivityLogSerializer(many=True),
            401: openapi.Response(
                description=(
                    "잘못된 요청 시 응답\n"
                    "- code:unauthorized 리스트에 접근할 인증이 완료되지 않았습니다."
                )
            ),
            403: openapi.Response(
                description=(
                    "잘못된 요청 시 응답\n"
                    "- code:forbidden 리스트에 접근할 권한이 없습니다."
                )
            ),
        },
    )
    # GET 요청 처리 = swagger용 (명시적으로 적어놈)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):

        queryset = super().get_queryset()

        # 관리자가 아닌 일반 사용자는 자신의 로그만 조회 가능
        if not self.request.user.is_superuser:
            queryset = queryset.filter(user_id=self.request.user)

        # 필터링 옵션
        action = self.request.query_params.get("action")
        if action:
            queryset = queryset.filter(action=action)

        start_date = self.request.query_params.get("start_date")
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        end_date = self.request.query_params.get("end_date")
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset


# 특정 로그 조회 API
class LogRetrieveAPIView(RetrieveAPIView):
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticatedJWTAuthentication]

    @swagger_auto_schema(
        security=[{"Bearer": []}],  # 토큰 인증
        responses={
            200: ActivityLogSerializer,  # many=True 제거함
            401: openapi.Response(
                description=(
                    "잘못된 요청 시 응답\n"
                    "- code:unauthorized 리스트에 접근할 인증이 완료되지 않았습니다."
                )
            ),
            403: openapi.Response(
                description=(
                    "잘못된 요청 시 응답\n"
                    "- code:forbidden 리스트에 접근할 권한이 없습니다."
                )
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        # 관리자가 아닌 일반 사용자는 자신의 로그만 조회 가능
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = queryset.filter(user_id=self.request.user)

        return queryset


# 클라이언트 ip 주소 획득 함수
def get_client_ip(request):
    """클라이언트의 IP 주소를 획득하는 유틸리티 함수"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip