from apps.ai.models import (
    FoodRequest,
    FoodResult,
    RecipeRequest,
    UserHealthRequest,
)
from rest_framework import serializers


# 레시피 추천 요청 시리얼라이저
class RecipeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeRequest
        fields = ["ingredients", "serving_size", "cooking_time", "difficulty"]

    def validate_ingredients(self, value):
        """재료가 비어있는지 확인"""
        if not value:
            raise serializers.ValidationError("적어도 하나 이상의 재료를 입력해주세요")
        return value


# 건강식단 추천 요청 시리얼라이저
class HealthRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserHealthRequest
        fields = ["weight", "goal", "exercise_frequency", "allergies", "disliked_foods"]


# 음식추천 요청 시리얼라이저
class FoodRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodRequest
        fields = ["cuisine_type", "food_base", "taste", "dietary_type"]


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


class MenuListChecksSerializer(serializers.ModelSerializer):
    """
    API 명세서 참조
    AI 추천 음식 유저별 리스트 조회
    admin일 경우 전체 리스트 조회
    """

    id = serializers.UUIDField(read_only=True)
    request_data = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = FoodResult
        fields = [
            "id",
            "user",
            "request_type",
            "request_data",
            "response_data",
            "created_at",
        ]

    def get_request_data(self, obj):
        try:
            request_obj = obj.request_object  # 3개 api 중 하나

            if obj.request_type == "RECIPE" and hasattr(request_obj, "ingredients"):
                return {
                    "ingredients": request_obj.ingredients,
                    "serving_size": request_obj.serving_size,
                    "cooking_time": request_obj.cooking_time,
                    "difficulty": request_obj.difficulty,
                }
            elif obj.request_type == "HEALTH" and hasattr(request_obj, "weight"):
                return {
                    "weight": request_obj.weight,
                    "exercise_frequency": request_obj.exercise_frequency,
                    "allergies": request_obj.allergies,
                    "disliked_foods": request_obj.disliked_foods,
                }
            elif obj.request_type == "FOOD" and hasattr(request_obj, "cuisine_type"):
                return {
                    "cuisine_type": request_obj.cuisine_type,
                    "food_base": request_obj.food_base,
                    "taste": request_obj.taste,
                    "dietary_type": request_obj.dietary_type,
                    "last_meal": request_obj.last_meal,
                }
            return {}
        except Exception:
            return {}
