from django.apps import AppConfig


class AiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai"


"""함수로 import시켜서 utils에 있는 시그널 다 불러옵니다"""
"""이것도 제가 수정한겁니다 ai 다 안 씀 코드 한줄 한줄 작성함 ^^"""

"""아래부터는 ai관련 리시버 모델 정의"""


def ready(self):
    import logging

    from apps.ai.models import (
        AIFoodRequest,
        AIFoodResult,
        AIRecipeRequest,
        AIUserHealthRequest,
    )
    from apps.log.models import ActivityLog
    from django.db.models.signals import post_save
    from django.dispatch import receiver

    logger = logging.getLogger(__name__)

    # 1번째 리시버
    @receiver(post_save, sender=AIFoodRequest)
    def log_ai_food_request(sender, instance, created, **kwargs):
        """AI 음식 추천 요청 로깅"""
        action_msg = "AI 음식 추천 요청 생성" if created else "AI 음식 추천 요청 수정"

        # 요청 타입에 따른 상세 메시지 구성
        request_type_msg = {
            "food": "음식 추천",
            "health": "건강 기반 추천",
            "recipe": "레시피 추천",
        }[instance.request_type]

        try:
            ActivityLog.objects.create(
                user_id=instance.user,
                action=ActivityLog.ActionType.AI_REQUEST,
                ip_address="0.0.0.0",
                user_agent="System",
                # 디테일 다 넣음
                details={
                    "message": f"{request_type_msg} {action_msg}",
                    "request_id": instance.id,
                    "request_type": instance.request_type,
                },
            )
            logger.info(f"AI 요청 로그 기록: {instance.id} - {request_type_msg}")
        except Exception as e:
            logger.error(f"AI 요청 로깅 중 오류 발생: {e}")

        # 2번째 리시버 #kwargs는 키워드 인자를 받는다고함 (관행이라고 해서 넣음) = 심지어 몰랐음 오늘암;; 관행이구나
        @receiver(post_save, sender=AIFoodResult)
        def log_ai_food_result(sender, instance, created, **kwargs):
            """AI 음식 추천 결과 로깅 = 이건 결과임 위에것과 다름"""
            if created:  # 결과가 생성될 때만 로깅
                try:
                    ActivityLog.objects.create(
                        user_id=instance.user,
                        action=ActivityLog.ActionType.AI_RESULT,
                        ip_address="0.0.0.0",
                        user_agent="System",
                        # 결과 안 넣으려고 했는데 이거 그냥 넣었습니다
                        details={
                            "message": f"AI {instance.get_request_type_display()} 결과 생성",
                            "food_name": instance.food_name,
                            "food_type": instance.food_type,
                            "request_type": instance.request_type,
                        },
                    )
                    logger.info(f"AI 결과 로그 기록: {instance.food_name}")
                except Exception as e:
                    logger.error(f"AI 결과 로깅 중 오류 발생: {e}")

        # 3번째 리시버
        @receiver(post_save, sender=AIRecipeRequest)
        def log_ai_recipe_request(sender, instance, created, **kwargs):
            """AI 레시피 요청 로깅 = 메인화면 레시피 추천"""
            action_msg = "AI 레시피 생성" if created else "AI 레시피 수정"
            try:
                ActivityLog.objects.create(
                    user_id=None,  # 레시피에는 사용자 정보가 없어서, 필요시 ai_request.user로 수정
                    action=ActivityLog.ActionType.AI_RECIPE,
                    ip_address="0.0.0.0",
                    user_agent="System",
                    details={
                        "message": action_msg,
                        "recipe_name": instance.name,
                        "recipe_id": str(instance.id),
                        "cuisine_type": instance.cuisine_type,
                        "meal_type": instance.meal_type,
                    },
                )
                logger.info(f"AI 레시피 로그 기록: {instance.name} ({instance.id})")
            except Exception as e:
                logger.error(f"AI 레시피 로깅 중 오류 발생: {e}")

        # 4번째 리시버
        @receiver(post_save, sender=AIUserHealthRequest)
        def log_ai_health_request(sender, instance, created, **kwargs):
            """AI 사용자 건강 정보를 통한 레시피 추천 로깅 = 건강 프로필"""
            action_msg = "건강 프로필 생성" if created else "건강 프로필 수정"
            try:
                ActivityLog.objects.create(
                    user_id=instance.user,
                    action=ActivityLog.ActionType.AI_HEALTH,
                    ip_address="0.0.0.0",
                    user_agent="System",
                    details={
                        "message": action_msg,
                        "goal": instance.get_goal_display(),
                        "exercise_frequency": instance.get_exercise_frequency_display(),
                    },
                )
                logger.info(f"사용자 {instance.user.id} 건강 프로필 로그 기록")
            except Exception as e:
                logger.error(f"건강 프로필 로깅 중 오류 발생: {e}")
