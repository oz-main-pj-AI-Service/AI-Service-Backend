import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class AIFoodRequest(models.Model):
    REQUEST_TYPE_CHOICES = (
        ("food", "음식 추천"),
        ("health", "건강 기반 추천"),
        ("recipe", "레시피 추천"),
    )

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="사용자", null=True
    )
    request_type = models.CharField(
        max_length=30, choices=REQUEST_TYPE_CHOICES, verbose_name="요청 유형"
    )
    request_data = models.JSONField(verbose_name="요청 데이터")
    response_data = models.JSONField(null=True, blank=True, verbose_name="응답 데이터")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 시간")

    class Meta:
        db_table = "AIFoodRequest"
        app_label = "ai"
        verbose_name = "AI 요청"
        verbose_name_plural = "AI 요청 목록"

    def __str__(self):
        return f"{self.user.email}의 {self.get_request_type_display()} 요청 ({self.id})"


class AIFoodResult(models.Model):
    REQUEST_TYPE_CHOICES = (
        ("food", "음식 추천"),
        ("health", "건강 기반 추천"),
        ("recipe", "레시피 추천"),
    )

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="사용자", null=True
    )
    request_type = models.CharField(
        max_length=30, choices=REQUEST_TYPE_CHOICES, verbose_name="요청 타입 유형"
    )
    food_name = models.CharField(max_length=100, verbose_name="음식명")
    food_type = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="음식 종류"
    )
    description = models.TextField(blank=True, verbose_name="설명")
    nutritional_info = models.JSONField(
        default=dict, blank=True, verbose_name="영양 정보"
    )
    recommendation_reason = models.TextField(blank=True, verbose_name="추천 이유")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 시간")

    class Meta:
        db_table = "AIFoodResult"
        app_label = "ai"
        verbose_name = "AI 추천 결과"
        verbose_name_plural = "AI 추천 결과 목록"

    def __str__(self):
        return f"{self.food_name} - {self.user.email}"


class AIRecipeRequest(models.Model):
    REQUEST_TYPE_CHOICES = (
        ("food", "음식 추천"),
        ("health", "건강 기반 추천"),
        ("recipe", "레시피 추천"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="레시피 이름")
    request_type = models.CharField(
        max_length=30, choices=REQUEST_TYPE_CHOICES, verbose_name="요청 유형"
    )
    description = models.TextField(verbose_name="레시피 설명")
    preparation_time = models.IntegerField(verbose_name="준비 시간(분)")
    cooking_time = models.IntegerField(verbose_name="조리 시간(분)")
    serving_size = models.IntegerField(verbose_name="제공 인원")
    difficulty = models.CharField(max_length=20, verbose_name="난이도")
    cuisine_type = models.CharField(
        max_length=50, verbose_name="요리 종류(한식/중식 등)"
    )
    meal_type = models.CharField(
        max_length=50, verbose_name="식사 종류(아침/점심/저녁)"
    )
    ingredients = models.JSONField(verbose_name="필요 재료 목록")
    instructions = models.JSONField(verbose_name="조리 순서")
    nutrition_info = models.JSONField(null=True, blank=True, verbose_name="영양 정보")
    is_ai_generated = models.BooleanField(default=False, verbose_name="AI 생성 여부")
    ai_request = models.ForeignKey(
        AIFoodRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="관련 AI 요청 ID",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="등록일")

    class Meta:
        db_table = "AIRecipeRequest"
        app_label = "ai"
        verbose_name = "AI 레시피 요청"
        verbose_name_plural = "AI 레시피 요청 목록"

    def __str__(self):
        return self.name


class AIUserHealthRequest(models.Model):
    class Goal(models.TextChoices):
        BULK_UP = "gain_muscle", "근육량 증가"
        DIET = "diet", "다이어트"
        MAINTENANCE = "maintenance", "유지"

    class ExerciseFrequency(models.TextChoices):
        NONE = "none", "운동안함"
        ONCE = "once", "주1회"
        TWO_TO_THREE = "two_to_three", "주2~3회"
        FOUR_TO_FIVE = "four_to_five", "주4~5회"

    REQUEST_TYPE_CHOICES = (
        ("food", "음식 추천"),
        ("health", "건강 기반 추천"),
        ("recipe", "레시피 추천"),
    )

    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name="사용자", null=True
    )
    request_type = models.CharField(
        max_length=30, choices=REQUEST_TYPE_CHOICES, verbose_name="요청 타입 유형"
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="몸무게 (kg)",
    )
    goal = models.CharField(
        max_length=20,
        choices=Goal.choices,
        default=Goal.MAINTENANCE,
        verbose_name="목표",
    )
    exercise_frequency = models.CharField(
        max_length=20,
        choices=ExerciseFrequency.choices,
        default=ExerciseFrequency.NONE,
        verbose_name="운동 빈도",
    )
    allergies = models.JSONField(default=list, blank=True, verbose_name="알레르기")
    disliked_foods = models.JSONField(
        default=list, blank=True, verbose_name="비선호 음식"
    )
    goal_start_date = models.DateField(
        null=True, blank=True, verbose_name="목표 시작일"
    )
    goal_end_date = models.DateField(null=True, blank=True, verbose_name="목표 종료일")

    class Meta:
        db_table = "AIUserHealthRequest"
        app_label = "ai"
        verbose_name = "AI 사용자 건강 요청"
        verbose_name_plural = "AI 사용자 건강 요청 목록"

    def __str__(self):
        return f"{self.user.email}의 건강 프로필"
