import json
import uuid
from datetime import datetime, timedelta

from apps.food.models import MealLog, UserGoal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

"""
MealLog 모델 테스트

1. 기본 생성 테스트: 모든 필드를 포함한 식사 기록 생성 및 검증
2. 문자열 표현 테스트: str 메서드 확인
3. 정렬 테스트: 식사 시간 내림차순 정렬 확인
4. JSON 필드 테스트: 복잡한 영양 정보 구조 저장 및 접근
5. CASCADE 테스트: 사용자 삭제 시 관련 식사 기록도 삭제되는지 확인

UserGoal 모델 테스트

1. 기본 생성 테스트: 모든 필드를 포함한 사용자 목표 생성 및 검증
2. 문자열 표현 테스트: str 메서드 확인
3. 정렬 테스트: 생성일 내림차순 정렬 확인
4. 선택 옵션 테스트: 목표 유형(GoalType) 선택 옵션 검증
5. JSON 필드 테스트: 복잡한 목표 메트릭 구조 저장 및 접근
6. 자동 시간 필드 테스트: auto_now_add와 auto_now 필드 동작 확인
7. CASCADE 테스트: 사용자 삭제 시 관련 목표도 삭제되는지 확인

"""

User = get_user_model()


class MealLogModelTest(TestCase):
    def setUp(self):
        # 테스트용 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="testpassword"
        )

        # 기본 테스트 데이터
        self.meal_time = timezone.now()
        self.meal_name = "닭가슴살 샐러드"
        self.meal_type = "점심"
        self.description = "닭가슴살200g 현미밥200g 아몬드8알"
        self.nutrition_info = {"calories": 500, "protein": 30, "carbs": 45, "fat": 25}

    # 밀로그 모델 생성 테스트
    def test_create_meal_log(self):
        meal_log = MealLog.objects.create(
            user_id=self.user,
            meal_name=self.meal_name,
            description=self.description,
            meal_time=self.meal_time,
            meal_type=self.meal_type,
            nutrition_info=self.nutrition_info,
        )

        # 데이터베이스에서 조회
        saved_meal = MealLog.objects.get(id=meal_log.id)

        # 기본 필드 검증
        self.assertEqual(saved_meal.user_id, self.user)
        self.assertEqual(saved_meal.meal_name, self.meal_name)
        self.assertEqual(saved_meal.description, self.description)
        self.assertEqual(saved_meal.meal_type, self.meal_type)
        self.assertEqual(saved_meal.nutrition_info, self.nutrition_info)

        # 날짜/시간 필드 검증 (마이크로초 차이가 있을 수 있으므로 날짜만 비교)
        self.assertEqual(saved_meal.meal_time.date(), self.meal_time.date())
        self.assertIsNotNone(saved_meal.created_at)

        # UUID 형식 검증
        self.assertIsInstance(saved_meal.id, uuid.UUID)

    # 밀로그 모델 문자열 표현 테스트
    def test_meal_log_str_method(self):
        """__str__ 메서드 테스트"""
        meal_log = MealLog.objects.create(
            user_id=self.user,
            meal_name=self.meal_name,
            meal_time=self.meal_time,
            meal_type=self.meal_type,
        )

        expected_str = f"{self.meal_name} - {meal_log.meal_time}"
        self.assertEqual(str(meal_log), expected_str)

    # 식사 시간 내림차순 테스트
    def test_meal_log_ordering(self):
        # 첫 번째 식사 기록 생성
        first_meal_time = timezone.now() - timedelta(hours=2)
        first_meal = MealLog.objects.create(
            user_id=self.user,
            meal_name="아침 식사",
            meal_time=first_meal_time,
            meal_type="아침",
        )

        # 두 번째 식사 기록 생성 (더 최근)
        second_meal_time = timezone.now()
        second_meal = MealLog.objects.create(
            user_id=self.user,
            meal_name="점심 식사",
            meal_time=second_meal_time,
            meal_type="점심",
        )

        # 모든 식사 기록 조회 (기본 정렬 순서 적용)
        meals = list(MealLog.objects.all())

        # 최신 식사 기록이 먼저 나와야 함
        self.assertEqual(meals[0], second_meal)
        self.assertEqual(meals[1], first_meal)

    # json 필드 테스트
    def test_nutrition_info_json_field(self):
        # 임의의 영양정보 구조
        complex_nutrition = {
            "calories": 500,
            "macros": {"protein": 35, "carbs": 50, "fat": 20},
            "vitamins": ["A", "C", "D", "E"],
            "minerals": {"calcium": 120, "iron": 5.2},
        }
        # 식사 기록 생성
        meal_log = MealLog.objects.create(
            user_id=self.user,
            meal_name=self.meal_name,
            meal_time=self.meal_time,
            meal_type=self.meal_type,
            nutrition_info=complex_nutrition,
        )

        saved_meal = MealLog.objects.get(id=meal_log.id)
        self.assertEqual(saved_meal.nutrition_info, complex_nutrition)

        # JSON 필드의 특정 값 접근 테스트
        self.assertEqual(saved_meal.nutrition_info["calories"], 500)
        self.assertEqual(saved_meal.nutrition_info["macros"]["protein"], 35)
        self.assertEqual(saved_meal.nutrition_info["vitamins"][1], "C")

    # 사용자 삭제 시 밀로그도 삭제되는지 확인
    def test_delete_user_cascades_meal_logs(self):
        # 식사 기록 생성
        meal_log = MealLog.objects.create(
            user_id=self.user,
            meal_name=self.meal_name,
            meal_time=self.meal_time,
            meal_type=self.meal_type,
        )

        meal_id = meal_log.id

        # 사용자 삭제
        self.user.delete()

        # 연결된 식사 기록도 삭제되었는지 확인
        with self.assertRaises(MealLog.DoesNotExist):
            MealLog.objects.get(id=meal_id)


# 사용자 목표 모델 테스트
class UserGoalModelTest(TestCase):
    # 위와 동일하게 진행함
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpassword"
        )

        # 기본 테스트 데이터
        self.goal_type = UserGoal.GoalType.DIET
        self.description = "체중 20kg 감량 목표"
        self.end_date = timezone.now() + timedelta(days=30)
        self.goal_metrics = {
            "target_weight": 74,
            "daily_calories": 2200,
            "weekly_exercise": 8,
        }

    def test_create_user_goal(self):
        user_goal = UserGoal.objects.create(
            user_id=self.user,
            goal_type=self.goal_type,
            description=self.description,
            end_date=self.end_date,
            is_active=True,
            goal_metrics=self.goal_metrics,
        )

        # 데이터베이스에서 조회
        saved_goal = UserGoal.objects.get(id=user_goal.id)

        # 기본 필드 검증
        self.assertEqual(saved_goal.user_id, self.user)
        self.assertEqual(saved_goal.goal_type, self.goal_type)
        self.assertEqual(saved_goal.description, self.description)
        self.assertEqual(saved_goal.is_active, True)
        self.assertEqual(saved_goal.goal_metrics, self.goal_metrics)

        # 날짜/시간 필드 검증
        self.assertEqual(saved_goal.end_date.date(), self.end_date.date())
        self.assertIsNotNone(saved_goal.start_date)
        self.assertIsNotNone(saved_goal.created_at)
        self.assertIsNotNone(saved_goal.updated_at)

        # UUID 형식 검증
        self.assertIsInstance(saved_goal.id, uuid.UUID)

    # str 메서드 테스트
    def test_user_goal_str_method(self):
        user_goal = UserGoal.objects.create(user_id=self.user, goal_type=self.goal_type)

        expected_str = f"{self.goal_type} - {self.user}"
        self.assertEqual(str(user_goal), expected_str)

    # 정렬 테스트 (위랑 똑같이 내림차순임)
    def test_user_goal_ordering(self):
        # 첫 번째 목표 생성
        first_goal = UserGoal.objects.create(
            user_id=self.user, goal_type=UserGoal.GoalType.DIET
        )

        # 잠시 대기 후 두 번째 목표 생성
        import time

        time.sleep(0.1)  # 100ms 대기

        second_goal = UserGoal.objects.create(
            user_id=self.user, goal_type=UserGoal.GoalType.MUSCLE_GAIN
        )

        # 모든 목표 조회 (기본 정렬 순서 적용)
        goals = list(UserGoal.objects.all())

        # 최신 목표가 먼저 나와야 함
        self.assertEqual(goals[0], second_goal)
        self.assertEqual(goals[1], first_goal)

    # 목표 유형 선택 옵션 테스트
    def test_goal_type_choices(self):
        # 유효한 목표 유형 생성
        diet_goal = UserGoal.objects.create(
            user_id=self.user, goal_type=UserGoal.GoalType.DIET
        )
        self.assertEqual(diet_goal.goal_type, "DIET")

        muscle_goal = UserGoal.objects.create(
            user_id=self.user, goal_type=UserGoal.GoalType.MUSCLE_GAIN
        )
        self.assertEqual(muscle_goal.goal_type, "MUSCLE_GAIN")

        balanced_goal = UserGoal.objects.create(
            user_id=self.user, goal_type=UserGoal.GoalType.BALANCED_NUTRITION
        )
        self.assertEqual(balanced_goal.goal_type, "BALANCED_NUTRITION")

    # json 필드 테스트
    def test_goal_metrics_json_field(self):
        # 임의 구조 목표
        complex_metrics = {
            "weight": {"current": 80, "target": 70, "weekly_goal": 0.5},
            "nutrition": {
                "daily_calories": 1800,
                "macros": {"protein": 120, "carbs": 180, "fat": 60},
            },
            "exercise": [
                {"day": "monday", "type": "cardio", "duration": 45},
                {"day": "wednesday", "type": "strength", "duration": 60},
                {"day": "friday", "type": "cardio", "duration": 45},
            ],
        }

        user_goal = UserGoal.objects.create(
            user_id=self.user, goal_type=self.goal_type, goal_metrics=complex_metrics
        )

        saved_goal = UserGoal.objects.get(id=user_goal.id)
        self.assertEqual(saved_goal.goal_metrics, complex_metrics)

        # JSON 필드의 특정 값 접근 테스트
        self.assertEqual(saved_goal.goal_metrics["weight"]["target"], 70)
        self.assertEqual(saved_goal.goal_metrics["nutrition"]["macros"]["protein"], 120)
        self.assertEqual(saved_goal.goal_metrics["exercise"][1]["type"], "strength")

    # 자동 시간 필드 테스트
    def test_auto_now_fields(self):
        user_goal = UserGoal.objects.create(user_id=self.user, goal_type=self.goal_type)

        # 최초 생성 시 created_at과 updated_at이 동일한지 확인
        self.assertIsNotNone(user_goal.created_at)
        self.assertIsNotNone(user_goal.updated_at)

        # 약간의 시간차를 두고 갱신
        import time

        time.sleep(0.1)  # 100ms 대기

        original_created_at = user_goal.created_at
        original_updated_at = user_goal.updated_at

        # 객체 업데이트
        user_goal.description = "새로운 설명"
        user_goal.save()

        # 데이터베이스에서 새로 조회
        updated_goal = UserGoal.objects.get(id=user_goal.id)

        # created_at은 변경되지 않고, updated_at만 변경되었는지 확인
        self.assertEqual(updated_goal.created_at, original_created_at)
        self.assertNotEqual(updated_goal.updated_at, original_updated_at)

    # 사용자 삭제 시 목표도 삭제되는지 확인
    def test_delete_user_cascades_goals(self):
        # 목표 생성
        user_goal = UserGoal.objects.create(user_id=self.user, goal_type=self.goal_type)

        goal_id = user_goal.id

        # 사용자 삭제
        self.user.delete()

        # 연결된 목표도 삭제되었는지 확인
        with self.assertRaises(UserGoal.DoesNotExist):
            UserGoal.objects.get(id=goal_id)
