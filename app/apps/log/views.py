from apps.log.models import ActivityLog
from apps.log.serializers import ActivityLogCreateSerializer, ActivityLogSerializer
from django.contrib.auth import get_user_model
from rest_framework import filters, permissions, status
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.exceptions import PermissionDenied, NotAuthenticated

User = get_user_model()

# 페이지 네이션 설정(10개로 해놨는데 필요에 따라 수정 가능)
class LogPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


# 관리자 또는 자신의 로그만 조회 가능한 권한 설정 (일반 사용자는 자신의 로그만 조회 가능)
class IsAdminOrSelf(permissions.BasePermission):

    def has_permission(self, request, view):
        # 먼저 인증 여부 확인
        if not request.user.is_authenticated:
            raise NotAuthenticated(detail="인증 실패", code="unauthorized")
        
        # 관리자는 모든 접근 허용
        if request.user.is_staff or request.user.is_superuser:
            return True

        # 일반유저가 'admin' URL에 접근하려는 경우, 관리자만 허용
        if "admin" in request.path:
            raise PermissionDenied(detail="권한 없음", code="forbidden")
        
        # 일반 사용자는 상태가 "ACTIVE"인 경우만 허용
        return request.user.status == "ACTIVE"


# 활동 로그 조회 및 생성 API
class LogListCreateView(ListCreateAPIView):
    queryset = ActivityLog.objects.all()
    pagination_class = LogPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["action", "ip_address", "user_agent"]
    ordering_fields = ["created_at", "action"]
    permission_classes = [IsAdminOrSelf]

    @swagger_auto_schema(
        security=[{'Bearer': []}], # 토큰 인증
        request_body = ActivityLogSerializer,
        responses={
            200: ActivityLogSerializer(many=True),
            401: openapi.Response(
                description=(
                    "잘못된 요청 시 응답\n"
                    "- code:unauthorized 리스트에 접근할 인증이 완료되지 않았습니다."
                )
            ),
            403: openapi.Response(
                description= (
                    "잘못된 요청 시 응답\n"
                    "- code:forbidden 리스트에 접근할 권한이 없습니다."
                )
            )
        }
    )
    # GET 요청 처리 = swagger용 (명시적으로 적어놈)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    # 시리얼라이저 설정
    def get_serializer_class(self):
        if self.request.method == "POST":
            return ActivityLogCreateSerializer
        return ActivityLogSerializer

    def get_queryset(self):
        
        queryset = super().get_queryset()

        # URL에서 log_id 확인
        log_id = self.kwargs.get("log_id")
        if log_id:
            return queryset.filter(id=log_id)

        # 관리자가 아닌 일반 사용자는 자신의 로그만 조회 가능
        if not self.request.user.is_superuser:
            queryset = queryset.filter(user_id=self.request.user.id)

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

    @swagger_auto_schema(
        security=[{'Bearer': []}],  # 토큰 인증
        request_body=ActivityLogCreateSerializer,
        responses={
            201: ActivityLogCreateSerializer,
            400: openapi.Response(
                description=(
                    "잘못된 요청 시 응답\n"
                    "- code:invalid_text 입력값 오류"
                )
            ),
            401: openapi.Response(
                description=(
                    "잘못된 요청 시 응답\n"
                    "- code:unauthorized 리스트에 접근할 인증이 완료되지 않았습니다."
                )
            ),
            403: openapi.Response(
                description= (
                    "잘못된 요청 시 응답\n"
                    "- code:forbidden 리스트에 접근할 권한이 없습니다."
                    )
            )
        }
    )
    
    # 로그 생성 API
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 로그 생성
        log = serializer.save(
            ip_address=get_client_ip(request),  # 공통 유틸리티 함수 사용
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            user_id=request.user if request.user.is_authenticated else None,
        )

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


# 특정 로그 조회 API
class LogRetrieveAPIView(RetrieveAPIView):
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAdminOrSelf]
    lookup_field = "id"
    lookup_url_kwarg = "log_id"

    @swagger_auto_schema(
        security=[{'Bearer': []}], # 토큰 인증
        request_body = ActivityLogSerializer,
        responses={
            200: ActivityLogSerializer, # many=True 제거함
            401: openapi.Response(
                description=(
                    "잘못된 요청 시 응답\n"
                    "- code:unauthorized 리스트에 접근할 인증이 완료되지 않았습니다."
                )
            ),
            403: openapi.Response(
                description= (
                    "잘못된 요청 시 응답\n"
                    "- code:forbidden 리스트에 접근할 권한이 없습니다."
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        # 관리자가 아닌 일반 사용자는 자신의 로그만 조회 가능
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = queryset.filter(user_id=self.request.user.id)

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
