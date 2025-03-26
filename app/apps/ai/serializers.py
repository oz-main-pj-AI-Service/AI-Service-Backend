from apps.ai.models import (
    AIFoodRequest,
    AIFoodResult,
    AIRecipeRequest,
    AIUserHealthRequest,
)
from rest_framework import serializers


# 레시피 추천 요청 시리얼라이저
class RecipeRequestSerializer(serializers.Serializer):
    ingredients = serializers.ListField(
        child=serializers.CharField(), help_text="요리에 사용할 재료 목록"
    )
    serving_size = serializers.CharField(help_text="몇 인분인지 (예: '2인분')")
    cooking_time = serializers.CharField(help_text="요리 시간 (분)")
    difficulty = serializers.ChoiceField(
        choices=AIRecipeRequest.w.choices,
        default=AIRecipeRequest.Difficulty.EASY,
        help_text="요리 난이도 (쉬움/중간/어려움)",
    )

    def validate_ingredients(self, value):
        """재료가 비어있는지 확인"""
        if not value:
            raise serializers.ValidationError("적어도 하나 이상의 재료를 입력해주세요")
        return value


# 건강식단 추천 요청 시리얼라이저
class HealthRequestSerializer(serializers.Serializer):
    weight = serializers.DecimalField(
        max_digits=5, decimal_places=2, help_text="몸무게 (kg)"
    )
    goal = serializers.ChoiceField(
        choices=AIUserHealthRequest.Goal.choices,
        help_text="목표 (벌크업/다이어트/유지)",
    )
    exercise_frequency = serializers.ChoiceField(
        choices=AIUserHealthRequest.ExerciseFrequency.choices,
        help_text="운동 빈도 (주1회/주2~3회/주4~5회/운동안함)",
    )
    allergies = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="알레르기 정보 (선택 사항)",
    )
    disliked_foods = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="비선호 음식 정보 (선택 사항)",
    )


# 음식추천 요청 시리얼라이저
class FoodRequestSerializer(serializers.Serializer):
    cuisine_type = serializers.CharField(
        required=True, help_text="음식 종류 (한식/중식/일식/양식/동남아)"
    )
    food_base = serializers.CharField(required=True, help_text="음식 기반 (면/밥/빵)")
    taste = serializers.CharField(
        required=True, help_text="맛 선호도 (단맛/고소한맛/매운맛/상큼한맛)"
    )
    dietary_type = serializers.CharField(
        required=True, help_text="식단 유형 (자극적/건강한 맛)"
    )
    last_meal = serializers.CharField(
        required=False, allow_blank=True, help_text="어제 먹은 음식 (선택 사항)"
    )


# 각 API 응답을 위한 시리얼라이저
class RecipeResponseSerializer(serializers.Serializer):
    """레시피 응답을 위한 시리얼라이저"""

    success = serializers.BooleanField(help_text="요청 성공 여부")
    recipe_id = serializers.CharField(help_text="생성된 레시피 ID")
    recipe = serializers.JSONField(help_text="레시피 정보")


class HealthResponseSerializer(serializers.Serializer):
    """건강 추천 응답을 위한 시리얼라이저"""

    success = serializers.BooleanField(help_text="요청 성공 여부")
    request_id = serializers.IntegerField(help_text="요청 ID")
    meal_plan = serializers.JSONField(help_text="식단 정보")


class FoodResponseSerializer(serializers.Serializer):
    """음식 추천 응답을 위한 시리얼라이저"""

    success = serializers.BooleanField(help_text="요청 성공 여부")
    request_id = serializers.IntegerField(help_text="요청 ID")
    recommendation = serializers.JSONField(help_text="추천 음식 정보")


class ErrorResponseSerializer(serializers.Serializer):
    """에러 응답을 위한 시리얼라이저"""

    error = serializers.CharField(help_text="에러 메시지")
    invalid_items = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="유효하지 않은 항목 목록",
    )
