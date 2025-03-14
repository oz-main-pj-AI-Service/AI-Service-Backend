import json
import uuid
from datetime import date, timedelta
from decimal import Decimal

from apps.ai.models import (
    AIFoodRequest,
    AIFoodResult,
    AIRecipeRequest,
    AIUserHealthRequest,
)
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class AIModelsTestCase(TestCase):
    def setUp(self):
        # 테스트용 사용자 생성 (이메일 기반)
        self.user = User.objects.create_user(
            email="test@example.com", password="testpassword123"
        )

        # AIFoodRequest 테스트 데이터
        self.food_request = AIFoodRequest.objects.create(
            user=self.user,
            request_type="food",
            request_data={
                "cuisine_type": "한식",
                "food_type": "밥",
                "taste": "매운맛",
                "dietary_type": "건강한 맛",
                "last_meal": "햄버거",
            },
        )

        # AIFoodResult 테스트 데이터
        self.food_result = AIFoodResult.objects.create(
            user=self.user,
            request_type="food",
            food_name="비빔밥",
            food_type="한식",
            description="신선한 야채와 고추장이 들어간 건강한 한식",
            nutritional_info={"calories": 500, "protein": 15, "carbs": 80, "fat": 10},
            recommendation_reason="매운맛을 선호하며 건강한 한식을 원하셨기 때문에 비빔밥을 추천합니다.",
        )

        # AIRecipeRequest 테스트 데이터
        self.recipe_request = AIRecipeRequest.objects.create(
            name="김치찌개",
            request_type="recipe",
            description="맛있는 김치찌개 레시피",
            preparation_time=15,
            cooking_time=30,
            serving_size=4,
            difficulty="중간",
            cuisine_type="한식",
            meal_type="저녁",
            ingredients=[
                {"name": "김치", "amount": "300g"},
                {"name": "돼지고기", "amount": "200g"},
                {"name": "두부", "amount": "1모"},
                {"name": "파", "amount": "2뿌리"},
            ],
            instructions=[
                {"step": 1, "description": "김치를 적당한 크기로 자른다."},
                {"step": 2, "description": "돼지고기를 썰어 준비한다."},
                {
                    "step": 3,
                    "description": "냄비에 물을 붓고 김치와 돼지고기를 넣고 끓인다.",
                },
                {"step": 4, "description": "두부를 넣고 5분간 더 끓인다."},
            ],
            nutrition_info={"calories": 450, "protein": 25, "carbs": 30, "fat": 20},
            is_ai_generated=True,
            ai_request=self.food_request,
        )

        # AIUserHealthRequest 테스트 데이터
        self.health_request = AIUserHealthRequest.objects.create(
            user=self.user,
            request_type="health",
            weight=Decimal("70.50"),
            goal=AIUserHealthRequest.Goal.DIET,
            exercise_frequency=AIUserHealthRequest.ExerciseFrequency.TWO_TO_THREE,
            allergies=["땅콩", "새우"],
            disliked_foods=["셀러리", "양파"],
            goal_start_date=date.today(),
            goal_end_date=date.today() + timedelta(days=90),
        )

    def test_ai_food_request_creation(self):
        """AIFoodRequest 생성 테스트"""
        self.assertEqual(self.food_request.user, self.user)
        self.assertEqual(self.food_request.request_type, "food")
        self.assertEqual(self.food_request.request_data["cuisine_type"], "한식")
        self.assertIsNone(self.food_request.response_data)

        # response_data 업데이트 테스트
        self.food_request.response_data = {"recommendation": "비빔밥"}
        self.food_request.save()
        self.assertEqual(self.food_request.response_data["recommendation"], "비빔밥")

    def test_ai_food_result_creation(self):
        """AIFoodResult 생성 테스트"""
        self.assertEqual(self.food_result.user, self.user)
        self.assertEqual(self.food_result.food_name, "비빔밥")
        self.assertEqual(self.food_result.nutritional_info["calories"], 500)

        # 영양 정보 업데이트 테스트
        updated_nutrition = self.food_result.nutritional_info
        updated_nutrition["sodium"] = 800
        self.food_result.nutritional_info = updated_nutrition
        self.food_result.save()

        refreshed_result = AIFoodResult.objects.get(id=self.food_result.id)
        self.assertEqual(refreshed_result.nutritional_info["sodium"], 800)

    def test_ai_recipe_request_creation(self):
        """AIRecipeRequest 생성 테스트"""
        self.assertEqual(self.recipe_request.name, "김치찌개")
        self.assertEqual(self.recipe_request.serving_size, 4)
        self.assertEqual(len(self.recipe_request.ingredients), 4)
        self.assertEqual(len(self.recipe_request.instructions), 4)
        self.assertTrue(isinstance(self.recipe_request.id, uuid.UUID))
        self.assertTrue(self.recipe_request.is_ai_generated)

        # 레시피 수정 테스트
        self.recipe_request.difficulty = "쉬움"
        self.recipe_request.save()

        refreshed_recipe = AIRecipeRequest.objects.get(id=self.recipe_request.id)
        self.assertEqual(refreshed_recipe.difficulty, "쉬움")

    def test_ai_user_health_request_creation(self):
        """AIUserHealthRequest 생성 테스트"""
        self.assertEqual(self.health_request.user, self.user)
        self.assertEqual(self.health_request.weight, Decimal("70.50"))
        self.assertEqual(self.health_request.goal, AIUserHealthRequest.Goal.DIET)
        self.assertEqual(len(self.health_request.allergies), 2)
        self.assertEqual(self.health_request.allergies[0], "땅콩")

        # 사용자 목표 업데이트 테스트
        self.health_request.goal = AIUserHealthRequest.Goal.BULK_UP
        self.health_request.save()

        refreshed_health = AIUserHealthRequest.objects.get(id=self.health_request.id)
        self.assertEqual(refreshed_health.goal, AIUserHealthRequest.Goal.BULK_UP)

    def test_string_representation(self):
        """각 모델의 문자열 표현 테스트"""
        self.assertIn(self.user.email, str(self.food_request))
        self.assertIn(self.food_result.food_name, str(self.food_result))
        self.assertEqual(str(self.recipe_request), "김치찌개")
        self.assertIn(self.user.email, str(self.health_request))

    def test_related_models(self):
        """모델 간 관계 테스트"""
        self.assertEqual(self.recipe_request.ai_request, self.food_request)
