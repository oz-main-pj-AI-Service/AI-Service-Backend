import json
import os
from unittest.mock import MagicMock, patch

# 모델 임포트
from apps.ai.models import (
    AIFoodRequest,
    AIFoodResult,
    AIRecipeRequest,
    AIUserHealthRequest,
)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

# 테스트 시작 시 API 키 확인
API_KEY = os.environ.get("GEMINI_API_KEY") or settings.GEMINI_API_KEY
print(f"API key is {'set' if API_KEY else 'NOT set'}")

# 모의 응답 데이터 생성
mock_recipe_response = MagicMock()
mock_recipe_response.text = json.dumps(
    {
        "name": "김치볶음밥",
        "description": "맛있는 김치볶음밥",
        "cuisine_type": "한식",
        "meal_type": "점심",
        "preparation_time": 10,
        "cooking_time": 20,
        "serving_size": 2,
        "difficulty": "쉬움",
        "ingredients": [
            {"name": "쌀", "amount": "2공기"},
            {"name": "김치", "amount": "1/2포기"},
        ],
        "instructions": [
            {"step": 1, "description": "재료 준비"},
            {"step": 2, "description": "볶기"},
        ],
        "nutrition_info": {"calories": 300, "protein": 5, "carbs": 60, "fat": 5},
    }
)

mock_health_response = MagicMock()
mock_health_response.text = json.dumps(
    {
        "daily_calorie_target": 1800,
        "protein_target": 120,
        "meals": [
            {
                "type": "아침",
                "food_name": "계란 샐러드",
                "food_type": "건강식",
                "description": "단백질이 풍부한 아침식사",
                "nutritional_info": {
                    "calories": 350,
                    "protein": 25,
                    "carbs": 20,
                    "fat": 15,
                },
            },
            {
                "type": "점심",
                "food_name": "닭가슴살 샐러드",
                "food_type": "건강식",
                "description": "가벼운 점심",
                "nutritional_info": {
                    "calories": 450,
                    "protein": 35,
                    "carbs": 30,
                    "fat": 15,
                },
            },
            {
                "type": "저녁",
                "food_name": "두부 스테이크",
                "food_type": "건강식",
                "description": "단백질이 풍부한 저녁",
                "nutritional_info": {
                    "calories": 500,
                    "protein": 40,
                    "carbs": 25,
                    "fat": 20,
                },
            },
        ],
        "recommendation_reason": "다이어트를 위한 고단백 저탄수화물 식단",
    }
)

mock_food_response = MagicMock()
mock_food_response.text = json.dumps(
    {
        "recommendations": [
            {
                "food_name": "김치찌개",
                "food_type": "한식",
                "description": "매콤한 김치찌개",
                "nutritional_info": {
                    "calories": 350,
                    "protein": 15,
                    "carbs": 20,
                    "fat": 20,
                },
                "recommendation_reason": "매운맛을 선호하는 사용자에게 추천",
            },
            {
                "food_name": "비빔밥",
                "food_type": "한식",
                "description": "건강한 비빔밥",
                "nutritional_info": {
                    "calories": 450,
                    "protein": 20,
                    "carbs": 65,
                    "fat": 10,
                },
                "recommendation_reason": "건강한 맛을 선호하는 사용자에게 추천",
            },
            {
                "food_name": "된장찌개",
                "food_type": "한식",
                "description": "고소한 된장찌개",
                "nutritional_info": {
                    "calories": 300,
                    "protein": 15,
                    "carbs": 20,
                    "fat": 15,
                },
                "recommendation_reason": "고소한 맛을 선호하는 사용자에게 추천",
            },
        ]
    }
)

# validate_ingredients 함수의 모의 반환값
mock_ingredients_valid_response = MagicMock()
mock_ingredients_valid_response.text = "[]"

mock_ingredients_invalid_response = MagicMock()
mock_ingredients_invalid_response.text = '["컴퓨터", "자동차"]'

User = get_user_model()


class AIApiTestCase(TestCase):
    def setUp(self):
        # 테스트용 사용자 생성
        self.user = User.objects.create_user(
            email="existing@example.com",
            nickname="test",
            password="test1234",
            phone_number="1234",
        )
        self.client = Client()

    @patch("google.generativeai.GenerativeModel.generate_content")
    def test_recipe_recommendation(self, mock_generate_content):
        """레시피 추천 API 테스트"""
        # 모의 API 응답 설정
        mock_generate_content.side_effect = [
            mock_ingredients_valid_response,
            mock_recipe_response,
        ]

        url = "/api/ai/recipe-recommendation/"
        data = {
            "ingredients": ["쌀", "김치", "참기름", "계란"],
            "serving_size": 2,
            "cooking_time": 30,
            "difficulty": "보통",
        }

        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # 응답 확인 및 디버깅
        print(f"Recipe Response Status: {response.status_code}")
        result = response.json()

        self.assertEqual(response.status_code, 200)

        # 데이터베이스에 저장되었는지 확인
        request_count = AIFoodRequest.objects.filter(request_type="recipe").count()
        recipe_count = AIRecipeRequest.objects.all().count()
        self.assertGreater(request_count, 0)
        self.assertGreater(recipe_count, 0)

    @patch("google.generativeai.GenerativeModel.generate_content")
    def test_invalid_ingredients(self, mock_generate_content):
        """잘못된 식재료 검증 테스트"""
        # 모의 API 응답 설정
        mock_generate_content.return_value = mock_ingredients_invalid_response

        url = "/api/ai/recipe-recommendation/"
        data = {
            "ingredients": ["쌀", "김치", "컴퓨터", "자동차"],  # 잘못된 식재료 포함
            "serving_size": 2,
            "cooking_time": 30,
        }

        {
            "ingredients": ["안녕 나는 김이준이야"],  # 식재료가 아닌 대화형 발생
            "serving_size": 1,
            "cooking_time": 55,
        }

        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        print(f"Invalid Ingredients Status: {response.status_code}")
        if response.status_code == 400:
            result = response.json()
            self.assertTrue("error" in result)

    @patch("google.generativeai.GenerativeModel.generate_content")
    def test_health_recommendation(self, mock_generate_content):
        """건강 기반 음식 추천 API 테스트"""
        # 모의 API 응답 설정
        mock_generate_content.return_value = mock_health_response

        url = "/api/ai/health-recommendation/"
        data = {
            "weight": 70,
            "goal": "diet",
            "exercise_frequency": "two_to_three",
            "allergies": ["땅콩"],
            "disliked_foods": ["당근"],
        }

        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        print(f"Health Response Status: {response.status_code}")

        self.assertEqual(response.status_code, 200)

        # 데이터베이스에 저장되었는지 확인
        request_count = AIFoodRequest.objects.filter(request_type="health").count()
        health_profile_count = AIUserHealthRequest.objects.all().count()
        food_results_count = AIFoodResult.objects.filter(request_type="health").count()

        self.assertGreater(request_count, 0)
        self.assertGreater(health_profile_count, 0)
        self.assertGreater(food_results_count, 0)

    @patch("google.generativeai.GenerativeModel.generate_content")
    def test_food_recommendation(self, mock_generate_content):
        """음식 추천 API 테스트"""
        # 모의 API 응답 설정
        mock_generate_content.return_value = mock_food_response

        url = reverse("ai:recipe_recommendation")
        data = {
            "cuisine_type": "한식",
            "food_base": "밥",
            "taste": "매운맛",
            "dietary_type": "건강한 맛",
            "last_meal": "샐러드",
        }
        pass
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )
        print(response.json())
        print(f"Food Response Status: {response.status_code}")

        self.assertEqual(response.status_code, 200)

        # 데이터베이스에 저장되었는지 확인
        request_count = AIFoodRequest.objects.filter(request_type="food").count()
        food_results_count = AIFoodResult.objects.filter(request_type="food").count()

        self.assertGreater(request_count, 0)
        self.assertGreater(food_results_count, 0)

    def test_missing_required_fields(self):
        """필수 필드 누락 테스트"""
        # 레시피 추천 - ingredients 필드 누락
        url = "/api/ai/recipe-recommendation/"
        data = {"serving_size": 2, "cooking_time": 30}

        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        result = response.json()
        self.assertTrue("error" in result)


class APIErrorHandlingTestCase(TestCase):
    def setUp(self):
        # 테스트용 사용자 생성
        self.user = User.objects.create_user(
            email="admin@admin.com", password="12345678"
        )
        self.client = Client()

    def test_invalid_json(self):
        """잘못된 JSON 형식 테스트"""
        url = "/api/ai/recipe-recommendation/"
        # 잘못된 JSON 형식
        invalid_data = (
            "{ingredients: ['쌀', '김치'], serving_size: 2, cooking_time: 30}"
        )

        response = self.client.post(
            url, data=invalid_data, content_type="application/json"
        )

        print(f"Invalid JSON Status: {response.status_code}")

        self.assertEqual(response.status_code, 500)
        result = response.json()
        self.assertTrue("error" in result)
