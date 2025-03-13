from django.db import models
from django.conf import settings
import uuid

# 식사 기록을 저장하는 모델
class MealLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text='Meal Log ID')
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, help_text='사용자 ID')
    meal_name = models.CharField(max_length=50, help_text='음식명')
    description = models.TextField(null=True, blank=True, help_text='음식 설명')
    meal_time = models.DateTimeField(help_text='식사 시간')
    meal_type = models.CharField(max_length=50, help_text='식사 종류')
    nutrition_info = models.JSONField(null=True, blank=True, help_text='영양 정보')
    created_at = models.DateTimeField(auto_now_add=True, help_text='생성일')

    class Meta:
        db_table = 'meal_log'
        ordering = ['-meal_time']
    
    def __str__(self):
        return f"{self.meal_name} - {self.meal_time}"
    

# 사용자 목표 저장하는 모델
class UserGoal(models.Model):
        class GoalType(models.TextChoices):
            DIET = 'DIET', '다이어트'
            MUSCLE_GAIN = 'MUSCLE_GAIN', '근육량 증가'
            BALANCED_NUTRITION = 'BALANCED_NUTRITION', '균형잡힌 식단'
        
        id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text='User Goal ID')
        user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, help_text='사용자 ID')
        goal_type = models.CharField(max_length=30, choices=GoalType.choices, help_text='목표 선정(DIET, MUSCLE_GAIN, BALANCED_NUTRITION)')
        description = models.TextField(null=True, blank=True, help_text='목표 설명')
        start_date = models.DateTimeField(auto_now_add=True, help_text='목표 시작일')
        end_date = models.DateTimeField(null=True, blank=True, help_text='목표 마감일')
        is_active = models.BooleanField(default=False, help_text='진행중 여부')
        goal_metrics = models.JSONField(null=True, blank=True, help_text='구체적 목표 설정')
        created_at = models.DateTimeField(auto_now_add=True, help_text='생성 시간')
        updated_at = models.DateTimeField(auto_now=True, help_text='업데이트 시간')

        class Meta:
            db_table = 'user_goal'
            ordering = ['-created_at']
    
        def __str__(self):
            return f"{self.goal_type} - {self.user_id}"