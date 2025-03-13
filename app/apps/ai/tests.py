import json
from datetime import date, datetime, timedelta
from decimal import Decimal

from apps.ai.models import AiRequest, FoodResult, UserHealthProfile
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

User = get_user_model()


class AiRequestModelTest(TestCase):
    """AiRequest 모델 테스트"""

    def setUp(self):
        # 테스트용 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="testpassword"
        )

        # 테스트용 AI 요청 데이터
        self.request_data = {
            "ingredients": ["계란", "당근", "양파"],
            "meal_type": "점심",
            "cooking_time": 30,
        }

        # 테스트용 응답 데이터
        self.response_data = {
            "recipe_name": "계란 볶음밥",
            "instructions": "1. 계란을 풀어서 준비합니다...",
            "cooking_time": 25,
            "difficulty": "쉬움",
        }

    def test_create_ai_request(self):
        """AiRequest 객체 생성 테스트"""
        ai_request = AiRequest.objects.create(
            user=self.user,
            request_type=AiRequest.RequestType.RECIPE,
            request_data=self.request_data,
            response_data=self.response_data,
        )

        self.assertEqual(ai_request.user, self.user)
        self.assertEqual(ai_request.request_type, AiRequest.RequestType.RECIPE)
        self.assertEqual(ai_request.request_data, self.request_data)
        self.assertEqual(ai_request.response_data, self.response_data)
        self.assertTrue(isinstance(ai_request.created_at, datetime))

    def test_ai_request_str_method(self):
        """AiRequest __str__ 메서드 테스트"""
        ai_request = AiRequest.objects.create(
            user=self.user,
            request_type=AiRequest.RequestType.RECIPE,
            request_data=self.request_data,
        )

        expected_str = f"레시피 추천 - {self.user.email} - {ai_request.created_at.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(ai_request), expected_str)

    def test_ai_request_ordering(self):
        """AiRequest 객체 정렬 순서 테스트 (최신순)"""
        # 첫 번째 요청 생성
        first_request = AiRequest.objects.create(
            user=self.user,
            request_type=AiRequest.RequestType.RECIPE,
            request_data=self.request_data,
        )

        # 약간의 시간 간격을 두고 두 번째 요청 생성
        second_request = AiRequest.objects.create(
            user=self.user,
            request_type=AiRequest.RequestType.MEAL_PLAN,
            request_data={"days": 7, "goal": "diet"},
        )

        # 정렬 순서 확인 (최신순)
        ai_requests = AiRequest.objects.all()
        self.assertEqual(ai_requests[0], second_request)
        self.assertEqual(ai_requests[1], first_request)


class UserHealthProfileModelTest(TestCase):
    """UserHealthProfile 모델 테스트"""

    def setUp(self):
        # 테스트용 사용자 생성 - username 제거
        self.user = User.objects.create_user(
            email="health@example.com", password="healthpassword"
        )

        # 알레르기 및 비선호 음식 데이터
        self.allergies = ["땅콩", "새우", "밀가루"]
        self.disliked_foods = ["브로콜리", "가지"]

        # 목표 시작일 및 종료일
        self.start_date = date.today()
        self.end_date = self.start_date + timedelta(days=30)

    def test_create_health_profile(self):
        """UserHealthProfile 객체 생성 테스트"""
        profile = UserHealthProfile.objects.create(
            user=self.user,
            weight=Decimal("68.5"),
            goal=UserHealthProfile.Goal.DIET,
            exercise_frequency=UserHealthProfile.ExerciseFrequency.MODERATE,
            allergies=self.allergies,
            disliked_foods=self.disliked_foods,
            goal_start_date=self.start_date,
            goal_end_date=self.end_date,
        )

        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.weight, Decimal("68.5"))
        self.assertEqual(profile.goal, UserHealthProfile.Goal.DIET)
        self.assertEqual(
            profile.exercise_frequency, UserHealthProfile.ExerciseFrequency.MODERATE
        )
        self.assertEqual(profile.allergies, self.allergies)
        self.assertEqual(profile.disliked_foods, self.disliked_foods)
        self.assertEqual(profile.goal_start_date, self.start_date)
        self.assertEqual(profile.goal_end_date, self.end_date)

    def test_health_profile_defaults(self):
        """UserHealthProfile 기본값 테스트"""
        profile = UserHealthProfile.objects.create(user=self.user)

        self.assertEqual(profile.goal, UserHealthProfile.Goal.MAINTENANCE)
        self.assertEqual(
            profile.exercise_frequency, UserHealthProfile.ExerciseFrequency.NONE
        )
        self.assertEqual(profile.allergies, [])
        self.assertEqual(profile.disliked_foods, [])
        self.assertIsNone(profile.weight)
        self.assertIsNone(profile.goal_start_date)
        self.assertIsNone(profile.goal_end_date)

    def test_health_profile_str_method(self):
        """UserHealthProfile __str__ 메서드 테스트"""
        profile = UserHealthProfile.objects.create(user=self.user)

        expected_str = f"{self.user.email}의 건강 프로필"
        self.assertEqual(str(profile), expected_str)

    def test_user_health_profile_one_to_one(self):
        """UserHealthProfile과 User의 1:1 관계 테스트"""
        # 첫 번째 프로필 생성
        profile1 = UserHealthProfile.objects.create(
            user=self.user, weight=Decimal("70.0")
        )

        # 같은 사용자로 두 번째 프로필 생성 시도 시 예외 발생해야 함
        with self.assertRaises(Exception):  # 일반적으로 IntegrityError가 발생함
            profile2 = UserHealthProfile.objects.create(
                user=self.user, weight=Decimal("71.0")
            )


class FoodResultModelTest(TestCase):
    """FoodResult 모델 테스트"""

    def setUp(self):
        # 테스트용 사용자 생성 - username 제거
        self.user = User.objects.create_user(
            email="food@example.com", password="foodpassword"
        )

        # 테스트용 AI 요청 생성
        self.ai_request = AiRequest.objects.create(
            user=self.user,
            request_type=AiRequest.RequestType.FOOD_RECOMMENDATION,
            request_data={"meal_type": "점심", "preference": "한식"},
        )

        # 영양 정보 데이터
        self.nutritional_info = {"calories": 350, "protein": 15, "carbs": 45, "fat": 10}

    def test_create_food_result(self):
        """FoodResult 객체 생성 테스트"""
        food_result = FoodResult.objects.create(
            user=self.user,
            ai_request=self.ai_request,
            food_name="비빔밥",
            food_type="한식",
            description="신선한 채소와 고기를 곁들인 건강한 한 그릇 식사",
            nutritional_info=self.nutritional_info,
            recommendation_reason="사용자의 다이어트 목표와 한식 선호도에 맞춘 추천",
        )

        self.assertEqual(food_result.user, self.user)
        self.assertEqual(food_result.ai_request, self.ai_request)
        self.assertEqual(food_result.food_name, "비빔밥")
        self.assertEqual(food_result.food_type, "한식")
        self.assertEqual(food_result.nutritional_info, self.nutritional_info)
        self.assertTrue(isinstance(food_result.created_at, datetime))

    def test_food_result_without_ai_request(self):
        """AI 요청 없이 FoodResult 객체 생성 테스트"""
        food_result = FoodResult.objects.create(
            user=self.user,
            food_name="샐러드",
            food_type="양식",
            nutritional_info={"calories": 180, "protein": 5, "carbs": 20, "fat": 8},
        )

        self.assertEqual(food_result.user, self.user)
        self.assertIsNone(food_result.ai_request)
        self.assertEqual(food_result.food_name, "샐러드")

    def test_food_result_str_method(self):
        """FoodResult __str__ 메서드 테스트"""
        food_result = FoodResult.objects.create(user=self.user, food_name="된장찌개")

        expected_str = f"{self.user.email} - 된장찌개 - {food_result.created_at.strftime('%Y-%m-%d')}"
        self.assertEqual(str(food_result), expected_str)

    def test_food_result_ordering(self):
        """FoodResult 객체 정렬 순서 테스트 (최신순)"""
        # 첫 번째 결과 생성
        first_result = FoodResult.objects.create(user=self.user, food_name="김치찌개")

        import time

        time.sleep(1)

        # 약간의 시간 간격을 두고 두 번째 결과 생성
        second_result = FoodResult.objects.create(user=self.user, food_name="된장찌개")

        # 정렬 순서 확인 (최신순)
        food_results = FoodResult.objects.all()
        self.assertEqual(food_results[0], second_result)
        self.assertEqual(food_results[1], first_result)
