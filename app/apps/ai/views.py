import json

from apps.ai.models import (
    FoodRequest,
    FoodResult,
    RecipeRequest,
    UserHealthRequest,
)
from apps.ai.serializers import (
    FoodRequestSerializer,
    HealthRequestSerializer,
    MenuListChecksSerializer,
    RecipeRequestSerializer,
)
from apps.ai.service import (
    food_prompt,
    health_prompt,
    recipe_prompt,
    stream_food_prompt,
    stream_health_prompt,
    stream_recipe_prompt,
)
from apps.ai.utils import (
    clean_json_code_block,
    model,
    stream_response,
    validate_ingredients,
)
from apps.utils import pagination
from apps.utils.authentication import IsAuthenticatedJWTAuthentication
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.http import StreamingHttpResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

User = get_user_model()


class RecipeRecommendationView(APIView):
    """
    메인 페이지: 보유 식재료 기반 요리 추천 AI 시스템
    """

    permission_classes = [IsAuthenticatedJWTAuthentication]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        description="사용자가 입력한 식재료를 기반으로 요리 레시피를 추천",
        request_body=RecipeRequestSerializer,
        responses={
            200: openapi.Response(description="msg:레시피 추천 성공."),
            400: openapi.Response(
                description=(
                    "잘못된 요청 코드 \n"
                    "- `code`:`invalid_data`, 유효하지 않은 데이터입니다.\n"
                    "- `code`:`invalid_ingredients`, 유효하지 않은 식재료가 포함되어 있습니다."
                )
            ),
            500: openapi.Response(
                description="- `code`:`internal_error`, 서버 내부 오류가 발생했습니다.\n"
            ),
        },
    )
    def post(self, request):
        try:
            # 시리얼라이저로 요청 데이터 검증
            serializer = RecipeRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": serializer.errors, "code": "invalid_data"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 유효한 데이터 추출
            validated_data = serializer.validated_data
            ingredients = validated_data.get("ingredients", [])
            # 식재료 유효성 검사
            is_valid, invalid_items = validate_ingredients(ingredients)
            if not is_valid:
                return Response(
                    {
                        "error": "저는 식재료만 인식할 수 있어요🥲 식재료만 입력해주세요!",
                        "invalid_items": invalid_items,
                        "code": "invalid_ingredients",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # AI 요청 데이터 DB저장
            ai_request = serializer.save(user=request.user)

            # 스트리밍 모드 확인
            streaming_mode = (
                request.query_params.get("streaming", "false").lower() == "true"
            )

            # Gemini API 요청 프롬프트 구성
            if streaming_mode:
                prompt = stream_recipe_prompt(validated_data)

                # 스트리밍 응답 반환
                return StreamingHttpResponse(
                    stream_response(prompt, request, ai_request),
                    content_type="text/event-stream",
                )
            else:
                prompt = recipe_prompt(validated_data)

                # Gemini API 호출
                response = model.generate_content(prompt)

                try:
                    # JSON 파싱 시도
                    response_text = clean_json_code_block(response.text)

                    # JSON 파싱
                    ai_response_data = json.loads(response_text)

                    # 결과 저장
                    recipe = FoodResult.objects.create(
                        user=request.user,
                        content_type=ContentType.objects.get_for_model(RecipeRequest),
                        object_id=ai_request.pk,
                        response_data=ai_response_data,
                        request_type="RECIPE",
                    )

                    return Response(
                        {
                            "success": True,
                            "recipe_id": str(recipe.id),
                            "recipe": ai_response_data,
                        },
                        status=status.HTTP_200_OK,
                    )

                except json.JSONDecodeError:
                    # JSON 파싱 실패 시 원본 텍스트 반환
                    return Response(
                        {
                            "success": False,
                            "error": "AI 응답을 파싱할 수 없습니다.",
                            "raw_response": response.text,
                            "code": "internal_error",
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

        except Exception as e:
            return Response(
                {"error": str(e), "code": "internal_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class HealthBasedRecommendationView(APIView):
    """
    AI 목표 기반 추천: 건강 목표에 따른 음식 추천
    """

    permission_classes = [IsAuthenticatedJWTAuthentication]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        description="사용자의 건강 목표와 신체 정보를 기반으로 식단을 추천",
        request_body=HealthRequestSerializer,
        responses={
            200: openapi.Response(description="msg:건강 식단 추천 성공."),
            400: openapi.Response(
                description=(
                    "잘못된 요청 코드 \n"
                    "- `code`:`invalid_data`, 유효하지 않은 데이터입니다."
                )
            ),
            500: openapi.Response(
                description="- `code`:`internal_error`, 서버 내부 오류가 발생했습니다.\n"
            ),
        },
    )
    def post(self, request):
        try:
            # 시리얼라이저로 요청 데이터 검증
            serializer = HealthRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": serializer.errors, "code": "invalid_data"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 유효한 데이터 추출
            validated_data = serializer.validated_data

            ai_request = serializer.save(user=request.user)

            # 스트리밍 모드 확인
            streaming_mode = (
                request.query_params.get("streaming", "false").lower() == "true"
            )

            # 알레르기 및 비선호 음식 정보
            allergies = validated_data.get("allergies", [])
            disliked_foods = validated_data.get("disliked_foods", [])

            if streaming_mode:
                # 스트리밍용 프롬프트
                prompt = stream_health_prompt(validated_data, allergies, disliked_foods)
                # 스트리밍 응답 반환
                return StreamingHttpResponse(
                    stream_response(prompt, request, ai_request),
                    content_type="text/event-stream",
                )
            else:
                # 일반 JSON 응답용 프롬프트
                prompt = health_prompt(validated_data, allergies, disliked_foods)

                # Gemini API 호출
                response = model.generate_content(prompt)

                try:
                    # JSON 파싱 시도
                    response_text = clean_json_code_block(response.text)

                    # JSON 파싱
                    ai_response_data = json.loads(response_text)

                    # 결과 저장
                    health = FoodResult.objects.create(
                        user=request.user,
                        content_type=ContentType.objects.get_for_model(
                            UserHealthRequest
                        ),
                        object_id=ai_request.pk,
                        response_data=ai_response_data,
                        request_type="HEALTH",
                    )

                    return Response(
                        {
                            "success": True,
                            "request_id": ai_request.id,
                            "meal_plan": ai_response_data,
                        },
                        status=status.HTTP_200_OK,
                    )

                except json.JSONDecodeError:
                    # JSON 파싱 실패 시 원본 텍스트 반환
                    return Response(
                        {
                            "success": False,
                            "error": "AI 응답을 파싱할 수 없습니다.",
                            "raw_response": response.text,
                            "code": "internal_error",
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

        except Exception as e:
            return Response(
                {"error": str(e), "code": "internal_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FoodRecommendationView(APIView):
    """
    AI 기반 음식 추천: 사용자 선호도에 따른 음식 추천
    """

    permission_classes = [IsAuthenticatedJWTAuthentication]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        description="사용자의 음식 선호도를 기반으로 음식을 추천",
        request_body=FoodRequestSerializer,
        responses={
            200: openapi.Response(description="msg:음식 추천 성공."),
            400: openapi.Response(
                description=(
                    "잘못된 요청 코드 \n"
                    "- `code`:`invalid_data`, 유효하지 않은 데이터입니다."
                )
            ),
            500: openapi.Response(
                description="- `code`:`internal_error`, 서버 내부 오류가 발생했습니다.\n"
            ),
        },
    )
    def post(self, request):
        try:
            # 시리얼라이저로 요청 데이터 검증
            serializer = FoodRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": serializer.errors, "code": "invalid_data"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 유효한 데이터 추출
            validated_data = serializer.validated_data

            # AI 요청 데이터 저장
            ai_request = serializer.save(user=request.user)

            # 스트리밍 모드 확인
            streaming_mode = (
                request.query_params.get("streaming", "false").lower() == "true"
            )

            # 음식 선호도 정보 추출
            cuisine_type = validated_data.get("cuisine_type", "")
            food_base = validated_data.get("food_base", "")
            taste = validated_data.get("taste", "")
            dietary_type = validated_data.get("dietary_type", "")
            last_meal = validated_data.get("last_meal", "")

            if streaming_mode:
                # 스트리밍용 프롬프트
                prompt = stream_food_prompt(
                    cuisine_type, food_base, taste, dietary_type, last_meal
                )

                # 스트리밍 응답 반환
                return StreamingHttpResponse(
                    stream_response(prompt, request, ai_request),
                    content_type="text/event-stream",
                )
            else:
                # 일반 JSON 응답용 프롬프트
                prompt = food_prompt(
                    cuisine_type, food_base, taste, dietary_type, last_meal
                )

                # Gemini API 호출
                response = model.generate_content(prompt)

                try:
                    # JSON 파싱 시도
                    response_text = clean_json_code_block(response.text)

                    # JSON 파싱
                    ai_response_data = json.loads(response_text)

                    # 결과 저장
                    food = FoodResult.objects.create(
                        user=request.user,
                        content_type=ContentType.objects.get_for_model(FoodRequest),
                        object_id=ai_request.pk,
                        response_data=ai_response_data,
                        request_type="FOOD",
                    )

                    return Response(
                        {
                            "success": True,
                            "request_id": ai_request.id,
                            "recommendation": ai_response_data,
                        },
                        status=status.HTTP_200_OK,
                    )

                except json.JSONDecodeError:
                    # JSON 파싱 실패 시 원본 텍스트 반환
                    ai_request.response_data = {"raw_response": response.text}
                    ai_request.save()
                    return Response(
                        {
                            "success": False,
                            "error": "AI 응답을 파싱할 수 없습니다.",
                            "raw_response": response.text,
                            "code": "internal_error",
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

        except Exception as e:
            return Response(
                {"error": str(e), "code": "internal_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MenuRecommendListView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedJWTAuthentication]
    serializer_class = MenuListChecksSerializer
    pagination_class = pagination
    queryset = FoodResult.objects.all()

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        description="AI 추천 음식 유저별 리스트 조회 / admin일 경우 전체 리스트 조회",
        responses={
            200: openapi.Response(description="조회 가능 메세지 출력 x"),
            401: openapi.Response(
                description=("- `code`:`unauthorized`, 인증에 실패했습니다.\n")
            ),
            403: openapi.Response(
                description=("- `code`:`forbidden`, 접근 권한이 없습니다.\n")
            ),
            500: openapi.Response(
                description="- `code`:`internal_error`, 서버 내부 오류가 발생했습니다.\n"
            ),
        },
    )
    def get_queryset(self):
        try:
            # 관리자는 전체 조회 일반 사용자는 자신의 결과만
            if self.request.user.is_superuser:
                queryset = FoodResult.objects.all()
            else:
                queryset = FoodResult.objects.filter(user=self.request.user).all()
            # 응답 데이터 - API 명세서에 맞게 결과 리스트만 반환
            return queryset

        # 에러코드 401 / 403 / 500
        except AuthenticationFailed as e:
            return Response(
                {"error": "인증에 실패했습니다.", "code": "unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except PermissionDenied as e:
            return Response(
                {"error": "접근 권한이 없습니다.", "code": "forbidden"},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception as e:
            return Response(
                {"error": "서버 내부 오류가 발생했습니다.", "code": "internal_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
