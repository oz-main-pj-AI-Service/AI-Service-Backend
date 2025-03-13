from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

# 수정 완료
class AiRequest(models.Model):
    """AI 요청 정보를 관리하는 모델"""

    class RequestType(models.TextChoices):
        RECIPE = "recipe", _("레시피 추천")
        MEAL_PLAN = "meal_plan", _("식단 추천")
        FOOD_RECOMMENDATION = "food_recommendation", _("음식 추천")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_requests",
        verbose_name=_("사용자"),
    )
    request_type = models.CharField(
        max_length=30, choices=RequestType.choices, verbose_name=_("요청 유형")
    )
    request_data = models.JSONField(verbose_name=_("요청 데이터"))
    response_data = models.JSONField(
        verbose_name=_("응답 데이터"), null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("생성 시간"))

    class Meta:
        app_label = "ai"
        verbose_name = _("AI 요청")
        verbose_name_plural = _("AI 요청")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_request_type_display()} - {self.user.email} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class UserHealthProfile(models.Model):
    """사용자 건강 프로필 정보를 관리하는 모델"""

    class Goal(models.TextChoices):
        DIET = "diet", _("다이어트")
        BULK_UP = "bulk_up", _("벌크업")
        MAINTENANCE = "maintenance", _("유지어트")

    class ExerciseFrequency(models.TextChoices):
        NONE = "none", _("운동 안함")
        LIGHT = "light", _("가벼운 운동 (주 1-2회)")
        MODERATE = "moderate", _("중간 강도 운동 (주 3-4회)")
        ACTIVE = "active", _("활발한 운동 (주 5-6회)")
        # VERY_ACTIVE = 'very_active', _('매우 활발한 운동 (매일)') = 추가내용 삭제 가능

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="health_profile",
        verbose_name=_("사용자"),
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("몸무게 (kg)"),
    )
    goal = models.CharField(
        max_length=20,
        choices=Goal.choices,
        default=Goal.MAINTENANCE,
        verbose_name=_("목표"),
    )
    exercise_frequency = models.CharField(
        max_length=20,
        choices=ExerciseFrequency.choices,
        default=ExerciseFrequency.NONE,
        verbose_name=_("운동 빈도"),
    )
    allergies = models.JSONField(default=list, blank=True, verbose_name=_("알레르기"))
    disliked_foods = models.JSONField(
        default=list, blank=True, verbose_name=_("비선호 음식")
    )
    goal_start_date = models.DateField(
        null=True, blank=True, verbose_name=_("목표 시작일")
    )
    goal_end_date = models.DateField(
        null=True, blank=True, verbose_name=_("목표 종료일")
    )

    class Meta:
        verbose_name = _("사용자 건강 프로필")
        verbose_name_plural = _("사용자 건강 프로필")

    def __str__(self):
        return f"{self.user.email}의 건강 프로필"


class FoodResult(models.Model):
    """AI 음식 추천 결과를 저장하는 모델"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="food_recommendations",
        verbose_name=_("사용자"),
    )
    ai_request = models.ForeignKey(
        AiRequest,
        on_delete=models.CASCADE,
        related_name="food_recommendations",
        verbose_name=_("AI 요청"),
        null=True,
        blank=True,
    )
    food_name = models.CharField(max_length=100, verbose_name=_("음식명"))
    food_type = models.CharField(
        max_length=50, verbose_name=_("음식 종류"), null=True, blank=True
    )
    description = models.TextField(blank=True, verbose_name=_("설명"))
    nutritional_info = models.JSONField(
        default=dict, blank=True, verbose_name=_("영양 정보")
    )
    recommendation_reason = models.TextField(blank=True, verbose_name=_("추천 이유"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("생성 시간"))

    class Meta:
        verbose_name = _("음식 추천 결과")
        verbose_name_plural = _("음식 추천 결과")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.food_name} - {self.created_at.strftime('%Y-%m-%d')}"
