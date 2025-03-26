import uuid

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

User = get_user_model()


# 결과 저장 테이블
class FoodResult(models.Model):

    request_type_choice = (("RECIPE", "레시피"), ("HEALTH", "건강"), ("FOOD", "음식"))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Generic 관계 필드
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    request_object = GenericForeignKey("content_type", "object_id")
    request_type = models.CharField(choices=request_type_choice, max_length=8)

    response_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_foodresult"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.email}의 결과"


# 음식 요청
class FoodRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cuisine_type = models.CharField(max_length=20)
    food_base = models.CharField(max_length=100)
    taste = models.CharField(max_length=100)
    dietary_type = models.CharField(max_length=100)
    last_meal = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email}의 음식 요청"

    class Meta:
        db_table = "ai_foodrequest"
        ordering = ("-created_at",)


# 건강 기반 요청
class UserHealthRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    weight = models.FloatField(null=True, blank=True)
    exercise_frequency = models.CharField(max_length=100)
    allergies = models.JSONField(default=list, blank=True, verbose_name="알레르기")
    disliked_foods = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_userhealthrequest"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.email}의 건강 요청"


# 레시피 요청
class RecipeRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ingredients = models.JSONField(default=list, blank=True)
    serving_size = models.IntegerField(null=True, blank=True)
    cooking_time = models.IntegerField(null=True, blank=True)
    difficulty = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_reciperequest"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.email}의 레시피 요청"
