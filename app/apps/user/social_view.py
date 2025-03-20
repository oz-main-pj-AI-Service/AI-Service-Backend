import os
import urllib.parse

import requests
from apps.user.serializers import SocialUserCreateSerializer
from apps.utils.jwt_cache import store_access_token
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def check_user_create_or_login(user, email):
    if user and not user.is_social:  # 일반 로그인 계정이면
        return Response(
            {"error": "이 이메일은 포털 로그인으로 사용 중입니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if user:
        # 기존 사용자 로그인
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        store_access_token(user.id, access_token, 3600)  # redis 저장

        return Response(
            {
                "access_token": access_token,
                "refresh_token": str(refresh),
                "token_type": "Bearer",
                "expires_in": 3600,
            },
            status=status.HTTP_200_OK,
        )
    else:
        # 새로운 사용자 생성
        serializer = SocialUserCreateSerializer(data={"email": email})
        if serializer.is_valid():
            user = serializer.save()
            user.is_active = True
            user.save()
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            store_access_token(user.id, access_token, 3600)  # Redis에 저장

            return Response(
                {
                    "access_token": access_token,
                    "refresh_token": str(refresh),
                    "token_type": "Bearer",
                    "expires_in": 3600,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class GoogleSocialLoginView(APIView):
#     def get(self, request):
#         client_id = settings.GOOGLE_CLIENT_ID
#         redirect_uri = "http://127.0.0.1:8000/api/user/social-login/google/callback/"
#         scope = "email"
#         url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"
#         return redirect(url)


class GoogleSocialLoginCallbackView(APIView):

    def post(self, request):
        code = request.data.get("code")  # 구글이 주는 인가 코드
        code = urllib.parse.unquote(code)
        if not code:
            return Response({"error": "Authorization code is missing"}, status=400)

        client_id = settings.GOOGLE_CLIENT_ID
        client_secret = settings.GOOGLE_CLIENT_SECRET

        # 토큰 교환
        token_url = "https://oauth2.googleapis.com/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        response = requests.post(token_url, headers=headers, data=data)

        access_token = response.json().get("access_token")
        user_info_url = "https://openidconnect.googleapis.com/v1/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info = user_info_response.json()

        email = user_info.get("email")

        user = User.objects.filter(email=email).first()

        return check_user_create_or_login(user, email)


# class NaverSocialLoginView(APIView):
#     def get(self, request):
#         client_id = settings.NAVER_CLIENT_ID
#         redirect_uri = "http://127.0.0.1:8000/api/user/social-login/naver/callback/"
#         scope = "email"
#         state = "random_state"  # CSRF 보호를 위해 랜덤 상태 토큰 생성
#         url = f"https://nid.naver.com/oauth2.0/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}&state={state}"
#         return redirect(url)


class NaverSocialLoginCallbackView(APIView):
    def get(self, request):
        return Response({"error": "Method Not Allowed"}, status=405)

    def post(self, request):
        code = request.data.get("code")  # 네이버가 보내는 인가 코드
        if not code:
            return Response({"error": "Authorization code is missing"}, status=400)
        state = request.data.get("state")  # CSRF 보호를 위해 상태 토큰 확인

        # 토큰 교환
        token_url = "https://nid.naver.com/oauth2.0/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "state": state,
            "client_id": settings.NAVER_CLIENT_ID,
            "client_secret": settings.NAVER_CLIENT_SECRET,
        }
        print(settings.NAVER_CLIENT_ID)
        print(settings.NAVER_CLIENT_SECRET)
        response = requests.post(token_url, headers=headers, data=data)

        access_token = response.json().get("access_token")
        user_info_url = "https://openapi.naver.com/v1/nid/me"
        headers = {"Authorization": f"Bearer {access_token}"}

        user_info_response = requests.get(user_info_url, headers=headers)
        user_info = user_info_response.json()

        email = user_info.get("response", {}).get("email")

        user = User.objects.filter(email=email).first()

        return check_user_create_or_login(user, email)
