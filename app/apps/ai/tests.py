import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class AIRequestTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com",
            nickname="test",
            password="test1234",
            phone_number="1234",
        )

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        self.client = APIClient()
        self.recipe_url = reverse(
            "ai:recipe-recommendation"
        )  # URL 이름에 따라 다를 수 있음
        self.health_url = reverse("ai:health-recommendation")
        self.food_url = reverse("ai:food-recommendation")

        self.recipe_valid_data = {
            "ingredients": ["계란", "소금"],
            "serving_size": 2,
            "cooking_time": 10,
            "difficulty": "쉬움",
        }

        self.recipe_invalid_data = {"ingredients": "invalid_string"}

        self.health_valid_data = {
            "weight": 50,
            "goal": "다이어트",
            "exercise_frequency": "주 2회",
            "allergies": [],
            "disliked_foods": [],
        }

        self.food_valid_data = {
            "cuisine_type": "한식",
            "food_base": "고추장",
            "taste": "매운맛",
            "dietary_type": "자극적",
            "last_meal": "잔치국수",
        }

    # RECIPE REQUEST TEST
    def test_unauthorized_recipe_request(self):
        response = self.client.post(
            self.recipe_url, data=self.recipe_valid_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_data_format(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(
            self.recipe_url, data=self.recipe_invalid_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "invalid_data")

    @patch("apps.ai.views.model.generate_content")
    def test_invalid_ingredient_names(self, mock_generate):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # mock 응답 설정: Gemini가 비정상적인 항목을 감지했다고 응답하는 상황 시뮬레이션
        mock_response = MagicMock()
        mock_response.text = '["prompt", "eval", "코드 실행"]'
        mock_generate.return_value = mock_response

        data = {
            "ingredients": ["prompt", "eval", "코드 실행"],
            "difficulty": "쉬움",
        }

        response = self.client.post(self.recipe_url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "invalid_ingredients")

    @patch("apps.ai.views.GeminiClient.generate_content_recipe_prompt")
    def test_valid_recipe_request(self, mock_generate):
        mock_response = MagicMock()
        mock_response.text = """
        {
            "name": "계란찜",
            "description": "부드럽고 고소한 계란찜 레시피입니다."
        }
        """
        mock_generate.return_value = mock_response

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(
            self.recipe_url, data=self.recipe_valid_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("recipe", response.data)
        self.assertIn("description", response.data["recipe"])
        # 정상 응답이거나 Gemini API 실패 시 내부 오류로 떨어질 수 있음

    @patch("apps.ai.views.model.generate_content")  # stream=True 호출을 mock
    def test_recipe_streaming_mode(self, mock_generate_content):
        # 가짜 스트리밍 응답 생성 (리스트 형태로 여러 청크 흉내냄)
        mock_chunk_1 = MagicMock()
        mock_chunk_1.text = "요리 설명입니다. "

        mock_chunk_2 = MagicMock()
        mock_chunk_2.text = '###JSON###\n```json\n{"name": "계란찜", "description": "부드러운 계란찜 레시피"}\n```'

        mock_generate_content.return_value = [mock_chunk_1, mock_chunk_2]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(
            self.recipe_url + "?streaming=true",
            data=self.recipe_valid_data,
            format="json",
        )

        final_json_line = None
        for line in response.streaming_content:
            decoded_line = line.decode("utf-8").strip()
            if decoded_line.startswith("data: FINAL_JSON:"):
                final_json_line = decoded_line
                break

        self.assertIsNotNone(final_json_line, "FINAL_JSON 응답을 찾을 수 없습니다.")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/event-stream")

        json_part = final_json_line.replace("data: FINAL_JSON:", "").strip()
        data = json.loads(json_part)
        self.assertIn("name", data)
        self.assertIn("description", data)

    # FOOD REQUEST TEST
    def test_unauthorized_food_request(self):
        response = self.client.post(
            self.food_url, data=self.food_valid_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("apps.ai.views.GeminiClient.generate_content_food_prompt")
    def test_valid_food_request(self, mock_generate_content):
        mock_response = MagicMock()
        mock_response.text = """
        {
            "recommendation": {
                "food_name": "불고기덮밥",
                "food_type": "한식",
                "description": "달콤한 불고기와 밥이 조화를 이루는 한끼 식사입니다.",
                "nutritional_info": {
                    "fat": 15,
                    "carbs": 70,
                    "protein": 25,
                    "calories": 600
                },
                "recommendation_reason": "고단백, 고탄수 식단으로 라면 다음 식사로 적합합니다."
            }
        }
        """
        mock_generate_content.return_value = mock_response

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(
            self.food_url, data=self.food_valid_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            "nutritional_info", response.data["recommendation"]["recommendation"]
        )

    @patch("apps.ai.views.model.generate_content")
    def test_food_streaming_line_by_line(self, mock_generate_content):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # stream=True 인 경우 iterable 반환 (청크 여러 개 가능)
        mock_chunk = MagicMock()
        mock_chunk.text = (
            "안녕하세요\n"
            "###JSON###\n"
            "```json\n"
            "{\n"
            '  "recommendation": {\n'
            '    "food_name": "불고기덮밥",\n'
            '    "food_type": "한식",\n'
            '    "description": "맛있고 건강한 식사",\n'
            '    "nutritional_info": {\n'
            '      "fat": 20,\n'
            '      "carbs": 80,\n'
            '      "protein": 30,\n'
            '      "calories": 600\n'
            "    }\n"
            "  }\n"
            "}\n"
            "```"
        )
        mock_generate_content.return_value = iter([mock_chunk])

        response = self.client.post(
            self.food_url + "?streaming=true", data=self.food_valid_data, format="json"
        )

        final_json_line = None

        for line in response.streaming_content:
            decoded_line = line.decode("utf-8").strip()
            if decoded_line.startswith("data: FINAL_JSON:"):
                final_json_line = decoded_line
                break

        self.assertIsNotNone(final_json_line, "FINAL_JSON 응답을 찾을 수 없습니다.")

        json_part = final_json_line.replace("data: FINAL_JSON:", "").strip()
        data = json.loads(json_part)

        self.assertIn("recommendation", data)
        self.assertIn("nutritional_info", data["recommendation"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("apps.ai.views.GeminiClient.generate_content_health_prompt")
    def test_valid_health_request(self, mock_generate):
        mock_response = MagicMock()
        mock_response.text = """
        {
            "daily_calorie_target": 1500,
            "protein_target": 100,
            "meals": [
                {
                    "type": "아침",
                    "food_name": "고구마, 계란",
                    "nutritional_info": {
                        "fat": 10,
                        "carbs": 30,
                        "protein": 20,
                        "calories": 300
                    }
                },
                {
                    "type": "점심",
                    "food_name": "현미밥, 닭가슴살",
                    "nutritional_info": {
                        "fat": 15,
                        "carbs": 40,
                        "protein": 30,
                        "calories": 400
                    }
                }
            ]
        }
        """
        mock_generate.return_value = mock_response

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(
            self.health_url, data=self.health_valid_data, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("meal_plan", response.data)
        self.assertIn("daily_calorie_target", response.data["meal_plan"])
        self.assertIn("protein_target", response.data["meal_plan"])
        self.assertIn("meals", response.data["meal_plan"])
        self.assertTrue(
            any(
                "nutritional_info" in meals
                for meals in response.data["meal_plan"]["meals"]
            )
        )

    @patch("apps.ai.views.model.generate_content")
    def test_health_streaming_line_by_line(self, mock_generate_content):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # 스트리밍 응답처럼 iterable 구성
        mock_chunk = MagicMock()
        mock_chunk.text = (
            "응답입니다\n"
            "###JSON###\n"
            "```json\n"
            "{\n"
            '  "meals": [\n'
            "    {\n"
            '      "type": "아침",\n'
            '      "food_name": "고구마, 닭가슴살",\n'
            '      "nutritional_info": {\n'
            '        "fat": 10,\n'
            '        "carbs": 60,\n'
            '        "protein": 30,\n'
            '        "calories": 400\n'
            "      }\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "```"
        )
        mock_generate_content.return_value = iter([mock_chunk])

        response = self.client.post(
            self.health_url + "?streaming=true",
            data=self.health_valid_data,
            format="json",
        )

        final_json_line = None

        for line in response.streaming_content:
            decoded_line = line.decode("utf-8").strip()
            if decoded_line.startswith("data: FINAL_JSON:"):
                final_json_line = decoded_line
                break

        self.assertIsNotNone(final_json_line, "FINAL_JSON 응답을 찾을 수 없습니다.")

        json_part = final_json_line.replace("data: FINAL_JSON:", "").strip()
        data = json.loads(json_part)

        self.assertIn("meals", data)
        self.assertTrue(any("nutritional_info" in meal for meal in data["meals"]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_food_result_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        food_request = self.client.post(
            self.food_url, data=self.food_valid_data, format="json"
        )

        response = self.client.get(reverse("ai:food-result"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
