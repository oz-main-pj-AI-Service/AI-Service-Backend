from apps.ai.views import (
    FoodRecommendationView,
    HealthBasedRecommendationView,
    MenuRecommendListView,
    RecipeRecommendationView,
)
from django.urls.conf import path

app_name = "ai"

urlpatterns = [
    path(
        "recipe-recommendation/",
        RecipeRecommendationView.as_view(),
        name="recipe-recommendation",
    ),
    path(
        "health-recommendation/",
        HealthBasedRecommendationView.as_view(),
        name="health-recommendation",
    ),
    path(
        "food-recommendation/",
        FoodRecommendationView.as_view(),
        name="food-recommendation",
    ),
    path(
        "food-result/",
        MenuRecommendListView.as_view(),
        name="food-result",
    ),
]
