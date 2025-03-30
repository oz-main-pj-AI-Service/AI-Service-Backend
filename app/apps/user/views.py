import os
from ipaddress import ip_address

import jwt
from apps.user.serializers import (
    AccessTokenSerializer,
    RefreshTokenSerializer,
    UserChangePasswordSerializer,
    UserListSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserRegisterSerializer,
    UserUpdateSerializer,
    VerifyEmailSerializer,
)
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from ..log.models import ActivityLog  # 추가
from ..log.views import get_client_ip  # 추가
from ..utils.authentication import IsAuthenticatedJWTAuthentication
from ..utils.jwt_blacklist import add_to_blacklist, is_blacklisted
from ..utils.jwt_cache import get_refresh_token, store_access_token, store_refresh_token
from ..utils.pagination import Pagination
from ..utils.redis_block import (
    check_login_attempt_key,
    get_login_attempt_key,
    reset_login_attempt,
)

User = get_user_model()


class RefreshTokenView(APIView):
    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=RefreshTokenSerializer,
        responses={
            200: AccessTokenSerializer,
            400: openapi.Response(
                description=(
                    "잘못된 요청 시 응답\n"
                    "- `code`:`missing_refresh_token`: 리프레시 토큰이 없습니다.\n"
                    "- `code`:`token_blacklist`: 토큰이 블랙리스트에 등록되어 사용 불가합니다.\n"
                    "- `code`:`token_invalid`: 서버에 저장된 리프레시 토큰과 일치하지 않습니다."
                ),
            ),
            403: openapi.Response(
                description="- `code`:`Invalid_Refresh_Token`",
            ),
        },
    )
    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"error": ":Refresh Token is missing", "code": "missing_refresh_token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            # Refresh Token 검증
            refresh = RefreshToken(refresh_token)

            if is_blacklisted(str(refresh.access_token)):
                return Response(
                    {"error": "Token is blacklisted", "code": "token_blacklist"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user_id = refresh["user_id"]

            stored_refresh_token = get_refresh_token(user_id)
            if stored_refresh_token != refresh_token:
                return Response(
                    {"error": "Token is invalid", "code": "token_invalid"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 확인 끝 새로운 access token 발급
            new_access_token = str(refresh.access_token)
            store_access_token(user_id, new_access_token, 3600)
            return Response(
                {
                    "access_token": new_access_token,
                    "token_type": "bearer",
                    "expires_in": 3600,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"code": "Invalid_Refresh_Token", "message": str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )


class UserRegisterView(APIView):
    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=UserRegisterSerializer,
        responses={
            201: UserRegisterSerializer,
            400: openapi.Response(
                description=(
                    "잘못된 요청 시 응답\n"
                    "- `code`:`password_mismatch` , 비밀번호 불일치.\n"
                    "- `code`:`password_invalid` , 비밀번호 길이, 문자...\n"
                    "- `code`:`required_field_missing` , 필수 필드 누락.\n"
                ),
            ),
            409: openapi.Response(
                description=(
                    "- `code`:`email_conflict`, 이미 사용중인 이메일\n"
                    "- `code`:`social_user`, 이미 사용중인 이메일\n"
                    "- `code`:`phone_number_conflict`, 이미 사용중인 핸드폰 번호"
                )
            ),
        },
    )
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            id = str(user.id)
            if os.getenv("DOCKER_ENV", "false").lower() == "true":
                domain = "dev.hansang.ai.kr"
                scheme = "https"
            else:
                domain = "127.0.0.1:8000"
                scheme = "http"

            token = jwt.encode({"user_id": id}, settings.SECRET_KEY, algorithm="HS256")
            verify_url = f"{scheme}://{domain}/verify-email/?token={token}"
            send_mail(
                "이메일 인증을 완료해 주세요",
                f"다음 링크를 클릭, 이메일 인증을 완료해주세요: {verify_url}",
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            return Response(
                {"msg": "회원가입 성공. 이메일 인증을 진행해 주세요."},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=VerifyEmailSerializer,
        responses={
            200: VerifyEmailSerializer,
            400: openapi.Response(
                description=(
                    "잘못된 요청 시 응답\n"
                    "- `code`:`no_token` , 토큰이 안옴.\n"
                    "- `code`:`email_verified` , 이미 인증된 이메일.\n"
                    "- `code`:`token_expired` , 만료된 토큰.\n"
                    "- `code`:`invalid_token` , 잘못된 토큰.\n"
                    "- `code`:`UserDoesNotExist` , 존재하지 않는 유저.\n"
                ),
            ),
        },
    )
    def post(self, request):
        token = request.data.get("token")

        if not token:
            return Response(
                {"error": "토큰이 없습니다.", "code": "no_token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            decode = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=decode["user_id"])
            if user.email_verified:
                return Response(
                    {"message": "이미 인증된 계정입니다.", "code": "email_verified"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.email_verified = True
            user.is_active = True
            user.save()

            return Response(
                {"message": "이메일 인증이 완료되었습니다. 계정이 인증되었습니다."},
                status.HTTP_200_OK,
            )
        except jwt.ExpiredSignatureError:
            return Response(
                {"error": "토큰이 만료되었습니다.", "code": "token_expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except jwt.DecodeError:
            return Response(
                {"error": "잘못된 토큰입니다.", "code": "invalid_token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except User.DoesNotExist:
            return Response(
                {"error": "존재하지 않는 사용자입니다.", "code": "UserDoesNotExist"},
                status=status.HTTP_404_NOT_FOUND,
            )


class UserLoginView(APIView):
    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=UserLoginSerializer,
        responses={
            200: UserLoginSerializer,
            400: openapi.Response(
                description=(
                    "잘못된 요청 시 응답\n"
                    "- `code`:`missmatch` , 이메일 또는 비밀번호 불일치.\n"
                ),
            ),
            403: openapi.Response(
                description=(
                    "- `code`:`not_verified`, 인증되지 않은 이메일\n"
                    "- `code`:`Too_much_attempts`, 로그인 시도횟수 5회 초과 실패 5분 간 불가"
                )
            ),
        },
    )
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        check_login_attempt_key(email)

        user = authenticate(email=email, password=password)
        if not user:
            return Response(
                {
                    "error": "이메일 또는 비밀번호가 올바르지 않습니다.",
                    "code": "missmatch",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.email_verified:
            return Response(
                {
                    "error": "이메일 인증이 완료되지 않았습니다. 이메일을 확인해주세요.",
                    "code": "not_verified",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        store_access_token(user.id, access_token, 3600)
        store_refresh_token(user.id, str(refresh), 86400)

        # activity log 추가 = 로그인
        ActivityLog.objects.create(
            user_id=user,
            action="LOGIN",
            ip_address=get_client_ip(request),
        )

        reset_login_attempt(email)

        return Response(
            {
                "access_token": access_token,
                "refresh_token": str(refresh),
                "token_type": "Bearer",
                "expires_in": 3600,
            },
            status=status.HTTP_200_OK,
        )


class UserLogoutView(APIView):
    permission_classes = [IsAuthenticatedJWTAuthentication]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={
            200: "msg:로그아웃 되었습니다.",
            401: openapi.Response(
                description="- `code`:`unauthorized`, 인증되지 않은 사용자입니다\n"
            ),
            403: openapi.Response(
                description=(
                    "- `code`:`not_verified`, 인증되지 않은 이메일\n"
                    "- `code`:`forbidden`, 관리자가 아닙니다.\n"
                )
            ),
        },
    )
    def post(self, request):
        """로그아웃 시 Access Token을 블랙리스트에 추가"""
        access_token = request.auth  # 현재 요청에서 JWT 토큰 가져오기

        if access_token:
            # 토큰 만료 시간 가져오기 (Redis에서 자동 만료되도록 설정)
            expires_in = access_token.payload["exp"] - access_token.payload["iat"]
            add_to_blacklist(str(access_token), expires_in)

        # activity log 추가 = 로그아웃
        ActivityLog.objects.create(
            user_id=request.user,
            action="LOGOUT",
            ip_address=get_client_ip(request),
        )

        return Response({"message": "로그아웃 되었습니다."}, status=status.HTTP_200_OK)


class UserProfileView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticatedJWTAuthentication]
    serializer_class = UserProfileSerializer

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={
            200: "조회 성공",
            401: openapi.Response(
                description="- `code`:`unauthorized`, 인증되지 않은 사용자입니다\n"
            ),
            403: openapi.Response(
                description=(
                    "- `code`:`not_verified`, 인증되지 않은 이메일\n"
                    "- `code`:`forbidden`, 관리자가 아닙니다.\n"
                )
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={
            200: UserProfileSerializer,
            400: openapi.Response(
                description="- `code`:`only_num`, 핸드폰 숫자만 입력"
            ),
            401: openapi.Response(
                description="- `code`:`unauthorized`, 인증되지 않은 사용자입니다\n"
            ),
            403: openapi.Response(
                description=(
                    "- `code`:`not_verified`, 인증되지 않은 이메일\n"
                    "- `code`:`forbidden`, 관리자가 아닙니다.\n"
                )
            ),
        },
    )
    def patch(self, request, *args, **kwargs):
        response = super().patch(request, *args, **kwargs)

        # activity log 추가 = 프로필 업데이트
        ActivityLog.objects.create(
            user_id=request.user,
            action="UPDATE_PROFILE",
            ip_address=get_client_ip(request),
            details=response.data,  # 업데이트된 필드를 details에 저장
        )

        return response

    def get_object(self):
        # 현재 로그인 유저 반환
        return self.request.user

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={
            200: "user account deactivated",
            401: openapi.Response(
                description="- `code`:`unauthorized`, 인증되지 않은 사용자입니다\n"
            ),
            403: openapi.Response(
                description=(
                    "- `code`:`not_verified`, 인증되지 않은 이메일\n"
                    "- `code`:`forbidden`, 관리자가 아닙니다.\n"
                )
            ),
        },
    )
    def delete(self, request, *args, **kwargs):
        user = self.get_object()

        # 계정 삭제 전 로깅
        ActivityLog.objects.create(
            user_id=request.user,
            action="DELETE_PROFILE",  # 이 액션이 모델에 없다면 추가 필요
            ip_address=get_client_ip(request),
        )

        user.delete()
        return Response(
            {"message": "User account deactivated successfully"},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticatedJWTAuthentication]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={
            200: UserChangePasswordSerializer,
            400: openapi.Response(
                description=(
                    "- `code`:`password_mismatch`, pass1,pass2 불일치"
                    "- `code`:`old_password_mismatch`, 현재 비밀번호 불일치"
                )
            ),
            401: openapi.Response(
                description="- `code`:`unauthorized`, 인증되지 않은 사용자입니다\n"
            ),
            403: openapi.Response(
                description=(
                    "- `code`:`not_verified`, 인증되지 않은 이메일\n"
                    "- `code`:`forbidden`, 관리자가 아닙니다.\n"
                )
            ),
        },
    )
    def post(self, request):
        serializer = UserChangePasswordSerializer(
            data=request.data,
            instance=request.user,  # 기존 유저 객체 전달
            context={"request": request},  # 세션 업데이트 위해 request 추가
        )

        if serializer.is_valid():
            serializer.save()  # `update()` 메서드 호출됨
            return Response(
                {"message": "비밀번호가 성공적으로 변경되었습니다."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FindEmail(APIView):
    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={
            200: "phone_number:string",
            400: openapi.Response(
                description="- `code`:`DoesNotExist`, 존재하지 않는 핸드폰 번호"
            ),
        },
    )
    def post(self, request):
        user = User.objects.get(phone_number=request.data.get("phone_number"))
        if user:
            return Response(
                {"message": f"your email is {user.email}"}, status=status.HTTP_200_OK
            )
        return Response(
            {"error": "존재 하지 않는 핸드폰 번호입니다.", "code": "DoesNotExist"},
            status=status.HTTP_404_NOT_FOUND,
        )


class AdminUserListView(ListAPIView):
    pagination_class = Pagination
    permission_classes = [IsAuthenticatedJWTAuthentication]
    serializer_class = UserListSerializer

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={
            200: openapi.Response(
                description="유저 리스트 조회 성공",
                schema=UserListSerializer(many=True),
            ),
            401: openapi.Response(
                description="- `code`:`unauthorized`, 인증되지 않은 사용자입니다\n"
            ),
            403: openapi.Response(
                description="- `code`:`forbidden`, 관리자가 아닙니다.\n"
            ),
        },
    )
    def get(self, request):
        return super().get(request)


class AdminUserUpdateView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticatedJWTAuthentication]
    serializer_class = UserUpdateSerializer
    queryset = User.objects.all()

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={
            200: UserUpdateSerializer,
            401: openapi.Response(
                description="- `code`:`unauthorized`, 인증되지 않은 사용자입니다\n"
            ),
            403: openapi.Response(
                description="- `code`:`forbidden`, 관리자가 아닙니다.\n"
            ),
        },
    )
    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        prev_status = user.status

        response = super().patch(request, *args, **kwargs)

        if prev_status == "DELETED" and response.data.get("status") == "ACTIVE":
            User.restore_user(user.email)

        return response
