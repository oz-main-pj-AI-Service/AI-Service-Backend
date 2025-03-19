import os

import jwt
from apps.user.serializers import (
    UserChangePasswordSerializer,
    UserListSerializer,
    UserProfileSerializer,
    UserRegisterSerializer,
    UserUpdateSerializer,
)
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
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

from ..utils.jwt_blacklist import add_to_blacklist
from ..utils.jwt_cache import store_access_token

User = get_user_model()


class UserRegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.save()
            id = str(user.id)
            domain = (
                os.getenv("DOMAIN")
                if os.getenv("DOCKER_ENV", "false").lower() == "true"
                else "127.0.0.1:8000"
            )
            token = jwt.encode({"user_id": id}, settings.SECRET_KEY, algorithm="HS256")
            verify_url = f"http://{domain}/api/user/verify-email?token={token}"
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
    def get(self, request):
        token = request.GET.get("token")

        if not token:
            return Response(
                {"error": "토큰이 없습니다."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            decode = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=decode["user_id"])
            if user.email_verified:
                return Response(
                    {"message": "이미 인증된 계정입니다."},
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
                {"error": "토큰이 만료되었습니다."}, status=status.HTTP_400_BAD_REQUEST
            )
        except jwt.DecodeError:
            return Response(
                {"error": "잘못된 토큰입니다."}, status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist:
            return Response(
                {"error": "존재하지 않는 사용자입니다."},
                status=status.HTTP_404_NOT_FOUND,
            )


class UserLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(email=email, password=password)
        if not user:
            return Response(
                {"error": "이메일 또는 비밀번호가 올바르지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.email_verified:
            return Response(
                {"error": "이메일 인증이 완료되지 않았습니다. 이메일을 확인해주세요."},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        store_access_token(user.id, access_token, 3600)

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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """로그아웃 시 Access Token을 블랙리스트에 추가"""
        access_token = request.auth  # 현재 요청에서 JWT 토큰 가져오기

        if access_token:
            # 토큰 만료 시간 가져오기 (Redis에서 자동 만료되도록 설정)
            expires_in = access_token.payload["exp"] - access_token.payload["iat"]
            add_to_blacklist(str(access_token), expires_in)

        return Response({"message": "로그아웃 되었습니다."}, status=status.HTTP_200_OK)


class UserProfileView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        # 현재 로그인 유저 반환
        return self.request.user

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        user.delete()
        return Response(
            {"message": "User account deactivated successfully"},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

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
    def post(self, request):
        user = User.objects.filter(
            phone_number=request.data.get("phone_number")
        ).first()
        if user:
            return Response(
                {"message": f"your email is {user.email}"}, status=status.HTTP_200_OK
            )
        return Response(
            {"msg": "존재 하지 않는 핸드폰 번호입니다."},
            status=status.HTTP_404_NOT_FOUND,
        )


class AdminUserListView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = UserListSerializer


class AdminUserUpdateView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = UserUpdateSerializer
    queryset = User.objects.all()
