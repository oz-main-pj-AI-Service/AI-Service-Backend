# test_real_api.py 파일 생성
import json

import requests

BASE_URL = "http://127.0.0.1:8000/api"  # 서버 URL에 맞게 수정


def test_recipe():
    url = f"{BASE_URL}/ai/recipe-recommendation/"
    data = {
        "ingredients": ["쌀", "김치", "참기름", "계란"],
        "serving_size": 2,
        "cooking_time": 30,
    }

    response = requests.post(url, json=data)
    print("\n===== 레시피 추천 실제 응답 =====")
    print(f"상태 코드: {response.status_code}")

    try:
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except:
        print(f"응답 텍스트: {response.text}")
    print("=============================\n")


def test_health():
    url = f"{BASE_URL}/ai/health-recommendation/"
    data = {
        "weight": 70,
        "goal": "diet",
        "exercise_frequency": "two_to_three",
        "allergies": ["땅콩"],
        "disliked_foods": ["당근"],
    }

    response = requests.post(url, json=data)
    print("\n===== 건강 추천 실제 응답 =====")
    print(f"상태 코드: {response.status_code}")

    try:
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except:
        print(f"응답 텍스트: {response.text}")
    print("=============================\n")


def test_food():
    url = f"{BASE_URL}/ai/food-recommendation/"
    data = {
        "cuisine_type": "한식",
        "food_base": "밥",
        "taste": "매운맛",
        "dietary_type": "건강한 맛",
        "last_meal": "샐러드",
    }

    response = requests.post(url, json=data)
    print("\n===== 음식 추천 실제 응답 =====")
    print(f"상태 코드: {response.status_code}")

    try:
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except:
        print(f"응답 텍스트: {response.text}")
    print("=============================\n")


if __name__ == "__main__":
    # 서버가 실행 중이어야 합니다
    test_recipe()
    test_health()
    test_food()
