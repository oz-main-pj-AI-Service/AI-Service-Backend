import json

import google.generativeai as genai
from apps.ai.models import (
    AIFoodRequest,
    AIFoodResult,
    AIRecipeRequest,
    AIUserHealthRequest,
)
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

User = get_user_model()

# Google Gemini API 설정
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


# 식재료 유효성 검사 함수
def validate_ingredients(ingredients):
    """
    입력된 항목이 실제 식재료인지 검증합니다.

    Args:
        ingredients (list): 검증할 식재료 목록

    Returns:
        tuple: (유효성 여부, 유효하지 않은 항목 목록)
    """
    invalid_items = []

    # Gemini API로 식재료 유효성 검사
    prompt = f"""
    다음 목록에서 실제 요리에 사용되는 식재료가 아닌 항목이 있는지 확인해주세요:
    {', '.join(ingredients)}

    식재료가 아닌 항목만 JSON 배열 형식으로 반환해주세요. 
    모두 유효한 식재료라면 빈 배열을 반환하세요:

    예시 응답 형식:
    ["항목1", "항목2"]

    JSON 형식의 배열만 반환하고 다른 설명은 포함하지 마세요.
    """

    try:
        response = model.generate_content(prompt)

        # 코드 블록 제거 처리 추가
        response_text = response.text
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()

        result = json.loads(response_text)

        if isinstance(result, list) and len(result) > 0:
            invalid_items = result
            return False, invalid_items
        return True, []
    except Exception as e:
        # API 오류 시 기본적으로 모든 항목 허용
        return True, []


class RecipeRecommendationView(APIView):
    """
    메인 페이지: 보유 식재료 기반 요리 추천 AI 시스템
    """

    # permission_classes = [IsAuthenticated]  # 로그인 필요시 주석 해제

    def post(self, request):
        try:

            # JSON 파싱 오류를 명시적으로 처리
            try:
                data = request.data
            except Exception as json_error:
                return Response(
                    {"error": "잘못된 JSON 형식입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 필수 입력 필드 검증
            required_fields = ["ingredients", "serving_size", "cooking_time"]
            for field in required_fields:
                if field not in data:
                    return Response(
                        {"error": f"{field} 필드가 필요합니다."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # 식재료 유효성 검사
            ingredients = data.get("ingredients", [])
            is_valid, invalid_items = validate_ingredients(ingredients)

            if not is_valid:
                return Response(
                    {
                        "error": "저는 식재료만 인식할 수 있어요🥲 식재료만 입력해주세요!",
                        "invalid_items": invalid_items,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 선택적 필드에 기본값 설정
            difficulty = data.get("difficulty", "보통")

            # AI 요청 데이터 저장
            # 인증된 사용자가 있으면 사용, 없으면 None 사용
            user = request.user if request.user.is_authenticated else None

            ai_request = AIFoodRequest.objects.create(
                user=user, request_type="recipe", request_data=data
            )

            # Gemini API 요청 프롬프트 구성
            prompt = f"""
            다음 재료를 사용해서 요리 레시피를 만들어주세요:
            재료: {', '.join(data['ingredients'])}
            몇인분: {data['serving_size']}
            소요 시간: {data['cooking_time']}분
            난이도: {difficulty}

            다음 형식으로 반환해주세요:
            {{
                "name": "요리이름",
                "description": "간단한 요리 설명",
                "cuisine_type": "요리 종류(한식/중식 등)",
                "meal_type": "식사 종류(아침/점심/저녁)",
                "preparation_time": 준비시간(분),
                "cooking_time": 조리시간(분),
                "serving_size": 제공인원,
                "difficulty": "난이도",
                "ingredients": [
                    {{"name": "재료1", "amount": "양"}},
                    {{"name": "재료2", "amount": "양"}}
                ],
                "instructions": [
                    {{"step": 1, "description": "조리 단계 설명"}},
                    {{"step": 2, "description": "조리 단계 설명"}}
                ],
                "nutrition_info": {{
                    "calories": 칼로리,
                    "protein": 단백질(g),
                    "carbs": 탄수화물(g),
                    "fat": 지방(g)
                }}
            }}

            JSON 형식으로만 반환해주세요. 다른 텍스트나 설명은 포함하지 마세요.
            """

            # Gemini API 호출
            response = model.generate_content(prompt)

            try:
                # JSON 파싱 시도
                # Gemini API가 코드 블록(```json)으로 감싸진 응답을 반환하는 경우를 처리
                response_text = response.text

                # 코드 블록 삭제 (```json ... ``` 제거)
                if "```json" in response_text:
                    # ```json과 ``` 사이의 내용만 추출
                    response_text = (
                        response_text.split("```json")[1].split("```")[0].strip()
                    )

                # JSON 파싱
                recipe_data = json.loads(response_text)

                # AI 응답 저장
                ai_request.response_data = recipe_data
                ai_request.save()

                # 레시피 데이터 저장
                recipe = AIRecipeRequest.objects.create(
                    name=recipe_data["name"],
                    request_type="recipe",
                    description=recipe_data["description"],
                    preparation_time=recipe_data["preparation_time"],
                    cooking_time=recipe_data["cooking_time"],
                    serving_size=recipe_data["serving_size"],
                    difficulty=recipe_data["difficulty"],
                    cuisine_type=recipe_data["cuisine_type"],
                    meal_type=recipe_data["meal_type"],
                    ingredients=recipe_data["ingredients"],
                    instructions=recipe_data["instructions"],
                    nutrition_info=recipe_data.get("nutrition_info", {}),
                    is_ai_generated=True,
                    ai_request=ai_request,
                )

                return Response(
                    {
                        "success": True,
                        "recipe_id": str(recipe.id),
                        "recipe": recipe_data,
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
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HealthBasedRecommendationView(APIView):
    """
    AI 목표 기반 추천: 건강 목표에 따른 음식 추천
    """

    # permission_classes = [IsAuthenticated]  # 로그인 필요시 주석 해제

    def post(self, request):
        try:

            # JSON 파싱 오류를 명시적으로 처리
            try:
                data = request.data
            except Exception as json_error:
                return Response(
                    {"error": "잘못된 JSON 형식입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 필수 입력 필드 검증
            required_fields = ["weight", "goal", "exercise_frequency"]
            for field in required_fields:
                if field not in data:
                    return Response(
                        {"error": f"{field} 필드가 필요합니다."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # 알레르기 및 비선호 음식 정보
            allergies = data.get("allergies", [])
            disliked_foods = data.get("disliked_foods", [])

            # 인증된 사용자가 있으면 사용, 없으면 None 사용
            user = request.user if request.user.is_authenticated else None

            # 사용자 건강 프로필 저장 또는 업데이트
            if user:
                health_profile, created = AIUserHealthRequest.objects.update_or_create(
                    user=user,
                    defaults={
                        "request_type": "health",
                        "weight": data["weight"],
                        "goal": data["goal"],
                        "exercise_frequency": data["exercise_frequency"],
                        "allergies": allergies,
                        "disliked_foods": disliked_foods,
                    },
                )

            # AI 요청 데이터 저장
            ai_request = AIFoodRequest.objects.create(
                user=user, request_type="health", request_data=data
            )

            # Gemini API 요청 프롬프트 구성
            prompt = f"""
            다음 정보를 바탕으로 건강한 식단을 추천해주세요:
            체중: {data['weight']}kg
            목표: {data['goal']} (벌크업/다이어트/유지)
            운동 빈도: {data['exercise_frequency']} (주1회/주2~3회/주4~5회/운동안함)
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
                # Gemini API가 코드 블록(```json)으로 감싸진 응답을 반환하는 경우를 처리
                response_text = response.text

                # 코드 블록 삭제 (```json ... ``` 제거)
                if "```json" in response_text:
                    # ```json과 ``` 사이의 내용만 추출
                    response_text = (
                        response_text.split("```json")[1].split("```")[0].strip()
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
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FoodRecommendationView(APIView):
    """
    AI 기반 음식 추천: 사용자 선호도에 따른 음식 추천
    """

    # permission_classes = [IsAuthenticated]  # 로그인 필요시 주석 해제

    def post(self, request):
        try:

            # JSON 파싱 오류를 명시적으로 처리
            try:
                data = request.data
            except Exception as json_error:
                return Response(
                    {"error": "잘못된 JSON 형식입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 인증된 사용자가 있으면 사용, 없으면 None 사용
            user = request.user if request.user.is_authenticated else None

            # AI 요청 데이터 저장
            ai_request = AIFoodRequest.objects.create(
                user=user, request_type="food", request_data=data
            )

            # 음식 선호도 정보
            cuisine_type = data.get("cuisine_type", "")  # 한식/중식/일식/양식/동남아
            food_base = data.get("food_base", "")  # 면/밥/빵
            taste = data.get("taste", "")  # 단맛/고소한맛/매운맛/상큼한맛
            dietary_type = data.get("dietary_type", "")  # 자극적/건강한 맛
            last_meal = data.get("last_meal", "")  # 어제 먹은 음식

            # Gemini API 요청 프롬프트 구성
            prompt = f"""
            다음 조건에 맞는 음식을 추천해주세요:
            음식 종류: {cuisine_type if cuisine_type else '특별한 선호 없음'} (한식/중식/일식/양식/동남아)
            음식 기반: {food_base if food_base else '특별한 선호 없음'} (면/밥/빵)
            맛 선호도: {taste if taste else '특별한 선호 없음'} (단맛/고소한맛/매운맛/상큼한맛)
            식단 유형: {dietary_type if dietary_type else '특별한 선호 없음'} (자극적/건강한 맛)
            최근 식사: {last_meal if last_meal else '정보 없음'}

            다음 JSON 형식으로 3가지 추천 음식을 반환해주세요:
            {{
                "recommendations": [
                    {{
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
                    }},
                    {{
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
                    }},
                    {{
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
                ]
            }}

            JSON 형식으로만 반환해주세요. 다른 텍스트나 설명은 포함하지 마세요.
            """

            # Gemini API 호출
            response = model.generate_content(prompt)

            try:
                # JSON 파싱 시도
                # Gemini API가 코드 블록(```json)으로 감싸진 응답을 반환하는 경우를 처리
                response_text = response.text

                # 코드 블록 삭제 (```json ... ``` 제거)
                if "```json" in response_text:
                    # ```json과 ``` 사이의 내용만 추출
                    response_text = (
                        response_text.split("```json")[1].split("```")[0].strip()
                    )

                # JSON 파싱
                food_data = json.loads(response_text)

                # AI 응답 저장
                ai_request.response_data = food_data
                ai_request.save()

                # 각 추천 음식 정보 저장
                for recommendation in food_data["recommendations"]:
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
                        "recommendations": food_data,
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
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
