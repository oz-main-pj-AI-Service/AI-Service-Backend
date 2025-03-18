from apps.ai.views import (
    FoodRecommendationView,
    HealthBasedRecommendationView,
    RecipeRecommendationView,
)
from django.urls.conf import path

app_name = "ai"

urlpatterns = [
    path(
        "recipe-recommendation/",
        RecipeRecommendationView.as_view(),
        name="recipe_recommendation",
    ),
    path(
        "health-recommendation/",
        HealthBasedRecommendationView.as_view(),
        name="health_recommendation",
    ),
    path(
        "food-recommendation/",
        FoodRecommendationView.as_view(),
        name="food_recommendation",
    ),
]
