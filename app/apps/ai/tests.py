# import json
#
# from django.contrib.auth import get_user_model
# from django.urls import reverse
# from rest_framework import status
# from rest_framework.test import APIClient, APITestCase
# from rest_framework_simplejwt.tokens import RefreshToken
#
# User = get_user_model()
#
#
# class AIRequestTests(APITestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(
#             email="test@test.com",
#             nickname="test",
#             password="test1234",
#             phone_number="1234",
#         )
#
#         refresh = RefreshToken.for_user(self.user)
#         self.access_token = str(refresh.access_token)
#
#         self.client = APIClient()
#         self.recipe_url = reverse(
#             "ai:recipe-recommendation"
#         )  # URL 이름에 따라 다를 수 있음
#         self.health_url = reverse("ai:health-recommendation")
#         self.food_url = reverse("ai:food-recommendation")
#
#         self.recipe_valid_data = {
#             "ingredients": ["계란", "소금"],
#             "serving_size": 2,
#             "cooking_time": 10,
#             "difficulty": "쉬움",
#         }
#
#         self.recipe_invalid_data = {"ingredients": "invalid_string"}
#
#         self.health_valid_data = {
#             "weight": 50,
#             "goal": "다이어트",
#             "exercise_frequency": "주 2회",
#             "allergies": [],
#             "disliked_foods": [],
#         }
#
#         self.food_valid_data = {
#             "cuisine_type": "한식",
#             "food_base": "고추장",
#             "taste": "매운맛",
#             "dietary_type": "자극적",
#             "last_meal": "잔치국수",
#         }
#
#     # RECIPE REQUEST TEST
#     def test_unauthorized_recipe_request(self):
#         response = self.client.post(
#             self.recipe_url, data=self.recipe_valid_data, format="json"
#         )
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#
#     def test_invalid_data_format(self):
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
#         response = self.client.post(
#             self.recipe_url, data=self.recipe_invalid_data, format="json"
#         )
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(response.data["code"], "invalid_data")
#
#     def test_invalid_ingredient_names(self):
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
#         data = {
#             "ingredients": ["prompt", "eval", "코드 실행"],
#             "difficulty": "쉬움",
#         }
#         response = self.client.post(self.recipe_url, data=data, format="json")
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(response.data["code"], "invalid_ingredients")
#
#     def test_valid_recipe_request(self):
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
#         response = self.client.post(
#             self.recipe_url, data=self.recipe_valid_data, format="json"
#         )
#         self.assertIn(response.status_code, [status.HTTP_200_OK])
#         # 정상 응답이거나 Gemini API 실패 시 내부 오류로 떨어질 수 있음
#
#     def test_recipe_streaming_mode(self):
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
#         response = self.client.post(
#             self.recipe_url + "?streaming=true",
#             data=self.recipe_valid_data,
#             format="json",
#         )
#         final_json_line = None
#
#         for line in response.streaming_content:
#             decoded_line = line.decode("utf-8").strip()
#
#             if decoded_line.startswith("data: FINAL_JSON"):
#                 final_json_line = decoded_line
#                 break
#         self.assertIsNotNone(final_json_line, "FINAL_JSON 응답을 찾을 수 없습니다.")
#
#         # Streaming 응답은 200이면서 content_type이 "text/event-stream"인 경우
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response["Content-Type"], "text/event-stream")
#
#         json_part = final_json_line.replace("data: FINAL_JSON:", "").strip()
#         data = json.loads(json_part)
#         self.assertIn("name", data)
#         self.assertIn("description", data)
#
#     # FOOD REQUEST TEST
#     def test_unauthorized_food_request(self):
#         response = self.client.post(
#             self.food_url, data=self.food_valid_data, format="json"
#         )
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#
#     def test_valid_food_request(self):
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
#         response = self.client.post(
#             self.food_url, data=self.food_valid_data, format="json"
#         )
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn(
#             "nutritional_info", response.data["recommendation"]["recommendation"]
#         )
#
#     def test_food_streaming_line_by_line(self):
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
#
#         response = self.client.post(
#             self.food_url + "?streaming=true", data=self.food_valid_data, format="json"
#         )
#
#         final_json_line = None  # 여기에 저장해야 나중에 쓸 수 있음
#
#         for line in response.streaming_content:
#             decoded_line = line.decode("utf-8").strip()
#
#             if decoded_line.startswith("data: FINAL_JSON:"):
#                 final_json_line = decoded_line
#                 break
#
#         self.assertIsNotNone(final_json_line, "FINAL_JSON 응답을 찾을 수 없습니다.")
#
#         # JSON 파싱해서 검증
#         json_part = final_json_line.replace("data: FINAL_JSON:", "").strip()
#         data = json.loads(json_part)
#
#         self.assertIn("recommendation", data)
#         self.assertIn("nutritional_info", data["recommendation"])
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     # HEALTH REQUEST TEST
#     def test_unauthorized_health_request(self):
#         response = self.client.post(
#             self.health_url, data=self.health_valid_data, format="json"
#         )
#
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#
#     def test_valid_health_request(self):
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
#         response = self.client.post(
#             self.health_url, data=self.health_valid_data, format="json"
#         )
#
#         self.assertIn(response.status_code, [status.HTTP_200_OK])
#         self.assertIn("meal_plan", response.data)
#         self.assertIn("daily_calorie_target", response.data["meal_plan"])
#         self.assertIn("protein_target", response.data["meal_plan"])
#         self.assertIn("meals", response.data["meal_plan"])
#         self.assertTrue(
#             any(
#                 "nutritional_info" in meals
#                 for meals in response.data["meal_plan"]["meals"]
#             )
#         )
#
#     def test_health_streaming_line_by_line(self):
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
#
#         response = self.client.post(
#             self.health_url + "?streaming=true",
#             data=self.health_valid_data,
#             format="json",
#         )
#
#         final_json_line = None  # 여기에 저장해야 나중에 쓸 수 있음
#
#         for line in response.streaming_content:
#             decoded_line = line.decode("utf-8").strip()
#             print(decoded_line)
#             if decoded_line.startswith("data: FINAL_JSON:"):
#                 final_json_line = decoded_line
#                 break
#
#         self.assertIsNotNone(final_json_line, "FINAL_JSON 응답을 찾을 수 없습니다.")
#
#         # JSON 파싱해서 검증
#         json_part = final_json_line.replace("data: FINAL_JSON:", "").strip()
#         data = json.loads(json_part)
#
#         self.assertIn("meals", data)
#         self.assertTrue(any("nutritional_info" in meal for meal in data["meals"]))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     def test_get_food_result_list(self):
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
#
#         food_request = self.client.post(
#             self.food_url, data=self.food_valid_data, format="json"
#         )
#
#         response = self.client.get(reverse("ai:food-result"))
#
#         self.assertEqual(response.status_code, status.HTTP_200_OK)

