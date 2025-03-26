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
    RecipeRequestSerializer,
)
from apps.ai.service import recipe_prompt
from apps.ai.utils import model, stream_response, validate_ingredients
from apps.utils.authentication import IsAuthenticatedJWTAuthentication
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.http import StreamingHttpResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
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
            ai_request = serializer.save()

            # 스트리밍 모드 확인
            streaming_mode = (
                request.query_params.get("streaming", "false").lower() == "true"
            )

            # Gemini API 요청 프롬프트 구성
            if streaming_mode:
                prompt = recipe_prompt(validated_data)

                # 스트리밍 응답 반환
                return StreamingHttpResponse(
                    stream_response(prompt), content_type="text/event-stream"
                )
            else:
                prompt = recipe_prompt(validated_data)

                # Gemini API 호출
                response = model.generate_content(prompt)

                try:
                    # JSON 파싱 시도
                    response_text = response.text

                    # 코드 블록 삭제 (```json ... ``` 제거)
                    if "```json" in response_text:
                        response_text = (
                            response_text.split("```json")[1].split("```")[0].strip()
                        )
                    elif "```" in response_text:
                        response_text = (
                            response_text.split("```")[1].split("```")[0].strip()
                        )

                    # JSON 파싱
                    ai_response_data = json.loads(response_text)

                    # 결과 저장
                    recipe = FoodResult.objects.create(
                        user=request.user,
                        content_type=ContentType.objects.get_for_model(RecipeRequest),
                        object_id=ai_request.pk,
                        response_data=ai_response_data,
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

            # 인증된 사용자 확인
            user = request.user if request.user.is_authenticated else None

            # 사용자 건강 프로필 저장 또는 업데이트
            if user:
                health_profile, created = AIUserHealthRequest.objects.update_or_create(
                    user=user,
                    defaults={
                        "request_type": "health",
                        "weight": validated_data["weight"],
                        "goal": validated_data["goal"],
                        "exercise_frequency": validated_data["exercise_frequency"],
                        "allergies": validated_data.get("allergies", []),
                        "disliked_foods": validated_data.get("disliked_foods", []),
                    },
                )

            # AI 요청 데이터 저장
            ai_request = AIFoodRequest.objects.create(
                user=user, request_type="health", request_data=validated_data
            )

            # 스트리밍 모드 확인
            streaming_mode = (
                request.query_params.get("streaming", "false").lower() == "true"
            )

            # 알레르기 및 비선호 음식 정보
            allergies = validated_data.get("allergies", [])
            disliked_foods = validated_data.get("disliked_foods", [])

            if streaming_mode:
                # 스트리밍용 프롬프트
                prompt = f"""
                다음 정보를 바탕으로 건강한 식단을 추천해주세요:
                체중: {validated_data['weight']}kg
                목표: {validated_data['goal']} (벌크업/다이어트/유지)
                운동 빈도: {validated_data['exercise_frequency']} (주1회/주2~3회/주4~5회/운동안함)
                알레르기: {', '.join(allergies) if allergies else '없음'}
                비선호 음식: {', '.join(disliked_foods) if disliked_foods else '없음'}

                먼저 자연스러운 대화형으로 하루 식단 추천을 해주세요.
                그 후에 다음 형식으로 추천 정보를 JSON 형식으로 제공해주세요:

                ###JSON###
                {{
                    "daily_calorie_target": 하루 권장 칼로리,
                    "protein_target": 하루 단백질 목표(g),
                    "meals": [
                        {{
                            "type": "아침",
                            "food_name": "음식명",
                            "food_type": "음식 종류",
                            "description": "설명",
                            "nutritional_info": {{
                                "calories": 칼로리,
                                "protein": 단백질(g),
                                "carbs": 탄수화물(g),
                                "fat": 지방(g)
                            }}
                        }},
                        {{
                            "type": "점심",
                            "food_name": "음식명",
                            "food_type": "음식 종류",
                            "description": "설명",
                            "nutritional_info": {{
                                "calories": 칼로리,
                                "protein": 단백질(g),
                                "carbs": 탄수화물(g),
                                "fat": 지방(g)
                            }}
                        }},
                        {{
                            "type": "저녁",
                            "food_name": "음식명",
                            "food_type": "음식 종류",
                            "description": "설명",
                            "nutritional_info": {{
                                "calories": 칼로리,
                                "protein": 단백질(g),
                                "carbs": 탄수화물(g),
                                "fat": 지방(g)
                            }}
                        }}
                    ],
                    "recommendation_reason": "추천 이유 및 설명"
                }}
                """

                # 스트리밍 응답 반환
                return StreamingHttpResponse(
                    stream_response(prompt), content_type="text/event-stream"
                )
            else:
                # 일반 JSON 응답용 프롬프트
                prompt = f"""
                다음 정보를 바탕으로 건강한 식단을 추천해주세요:
                체중: {validated_data['weight']}kg
                목표: {validated_data['goal']} (벌크업/다이어트/유지)
                운동 빈도: {validated_data['exercise_frequency']} (주1회/주2~3회/주4~5회/운동안함)
                알레르기: {', '.join(allergies) if allergies else '없음'}
                비선호 음식: {', '.join(disliked_foods) if disliked_foods else '없음'}

                하루 3끼 식단(아침, 점심, 저녁)을 추천해주세요. 

                다음 JSON 형식으로 반환해주세요:
                {{
                    "daily_calorie_target": 하루 권장 칼로리,
                    "protein_target": 하루 단백질 목표(g),
                    "meals": [
                        {{
                            "type": "아침",
                            "food_name": "음식명",
                            "food_type": "음식 종류",
                            "description": "설명",
                            "nutritional_info": {{
                                "calories": 칼로리,
                                "protein": 단백질(g),
                                "carbs": 탄수화물(g),
                                "fat": 지방(g)
                            }}
                        }},
                        {{
                            "type": "점심",
                            "food_name": "음식명",
                            "food_type": "음식 종류",
                            "description": "설명",
                            "nutritional_info": {{
                                "calories": 칼로리,
                                "protein": 단백질(g),
                                "carbs": 탄수화물(g),
                                "fat": 지방(g)
                            }}
                        }},
                        {{
                            "type": "저녁",
                            "food_name": "음식명",
                            "food_type": "음식 종류",
                            "description": "설명",
                            "nutritional_info": {{
                                "calories": 칼로리,
                                "protein": 단백질(g),
                                "carbs": 탄수화물(g),
                                "fat": 지방(g)
                            }}
                        }}
                    ],
                    "recommendation_reason": "추천 이유 및 설명"
                }}

                JSON 형식으로만 반환해주세요. 다른 텍스트나 설명은 포함하지 마세요.
                """

                # Gemini API 호출
                response = model.generate_content(prompt)

                try:
                    # JSON 파싱 시도
                    response_text = response.text

                    # 코드 블록 삭제 (```json ... ``` 제거)
                    if "```json" in response_text:
                        response_text = (
                            response_text.split("```json")[1].split("```")[0].strip()
                        )
                    elif "```" in response_text:
                        response_text = (
                            response_text.split("```")[1].split("```")[0].strip()
                        )

                    # JSON 파싱
                    meal_data = json.loads(response_text)

                    # AI 응답 저장
                    ai_request.response_data = meal_data
                    ai_request.save()

                    # 각 식사 정보 저장
                    for meal in meal_data["meals"]:
                        AIFoodResult.objects.create(
                            user=user,
                            request_type="health",
                            food_name=meal["food_name"],
                            food_type=meal["food_type"],
                            description=meal["description"],
                            nutritional_info=meal["nutritional_info"],
                            recommendation_reason=meal_data["recommendation_reason"],
                        )

                    return Response(
                        {
                            "success": True,
                            "request_id": ai_request.id,
                            "meal_plan": meal_data,
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

            # 인증된 사용자 확인
            user = request.user if request.user.is_authenticated else None

            # AI 요청 데이터 저장
            ai_request = AIFoodRequest.objects.create(
                user=user, request_type="food", request_data=validated_data
            )

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
                prompt = f"""
                다음 조건에 맞는 음식을 추천해주세요:
                음식 종류: {cuisine_type if cuisine_type else '특별한 선호 없음'} (한식/중식/일식/양식/동남아)
                음식 기반: {food_base if food_base else '특별한 선호 없음'} (면/밥/빵)
                맛 선호도: {taste if taste else '특별한 선호 없음'} (단맛/고소한맛/매운맛/상큼한맛)
                식단 유형: {dietary_type if dietary_type else '특별한 선호 없음'} (자극적/건강한 맛)
                최근 식사: {last_meal if last_meal else '정보 없음'}

                먼저 자연스러운 대화형으로 음식 추천을 해주세요. 이유와 함께 설명해주세요.
                그 후에 다음 형식으로 추천 정보를 JSON 형식으로 제공해주세요 (1개만):

                ###JSON###
                {{
                    "recommendation": {{
                        "food_name": "음식명",
                        "food_type": "음식 종류",
                        "description": "음식 설명",
                        "nutritional_info": {{
                            "calories": 칼로리,
                            "protein": 단백질(g),
                            "carbs": 탄수화물(g),
                            "fat": 지방(g)
                        }},
                        "recommendation_reason": "추천 이유"
                    }}
                }}
                """

                # 스트리밍 응답 반환
                return StreamingHttpResponse(
                    stream_response(prompt), content_type="text/event-stream"
                )
            else:
                # 일반 JSON 응답용 프롬프트
                prompt = f"""
                다음 조건에 맞는 음식을 추천해주세요:
                음식 종류: {cuisine_type if cuisine_type else '특별한 선호 없음'} (한식/중식/일식/양식/동남아)
                음식 기반: {food_base if food_base else '특별한 선호 없음'} (면/밥/빵)
                맛 선호도: {taste if taste else '특별한 선호 없음'} (단맛/고소한맛/매운맛/상큼한맛)
                식단 유형: {dietary_type if dietary_type else '특별한 선호 없음'} (자극적/건강한 맛)
                최근 식사: {last_meal if last_meal else '정보 없음'}

                다음 JSON 형식으로 1가지 추천 음식을 반환해주세요:
                {{
                    "recommendation": {{
                        "food_name": "음식명",
                        "food_type": "음식 종류",
                        "description": "음식 설명",
                        "nutritional_info": {{
                            "calories": 칼로리,
                            "protein": 단백질(g),
                            "carbs": 탄수화물(g),
                            "fat": 지방(g)
                        }},
                        "recommendation_reason": "추천 이유"
                    }}
                }}

                JSON 형식으로만 반환해주세요. 다른 텍스트나 설명은 포함하지 마세요.
                """

                # Gemini API 호출
                response = model.generate_content(prompt)

                try:
                    # JSON 파싱 시도
                    response_text = response.text

                    # 코드 블록 삭제 (```json ... ``` 제거)
                    if "```json" in response_text:
                        response_text = (
                            response_text.split("```json")[1].split("```")[0].strip()
                        )
                    elif "```" in response_text:
                        response_text = (
                            response_text.split("```")[1].split("```")[0].strip()
                        )

                    # JSON 파싱
                    food_data = json.loads(response_text)

                    # AI 응답 저장
                    ai_request.response_data = food_data
                    ai_request.save()

                    # 추천 음식 정보 저장 (1개)
                    recommendation = food_data["recommendation"]
                    AIFoodResult.objects.create(
                        user=user,
                        request_type="food",
                        food_name=recommendation["food_name"],
                        food_type=recommendation["food_type"],
                        description=recommendation["description"],
                        nutritional_info=recommendation["nutritional_info"],
                        recommendation_reason=recommendation["recommendation_reason"],
                    )

                    return Response(
                        {
                            "success": True,
                            "request_id": ai_request.id,
                            "recommendation": food_data,
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
