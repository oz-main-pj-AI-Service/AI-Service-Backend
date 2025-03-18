import argparse
import json
import sys

import requests

BASE_URL = "http://127.0.0.1:8000/api"


def test_recipe(verbose=True, url_base=BASE_URL):
    """레시피 추천 API 테스트"""
    url = f"{url_base}/ai/recipe-recommendation/"
    data = {
        "ingredients": ["쌀", "김치", "참기름", "계란"],
        "serving_size": 2,
        "cooking_time": 30,
    }

    try:
        response = requests.post(url, json=data)

        if verbose:
            print("\n===== 레시피 추천 API 테스트 =====")
            print(f"요청 URL: {url}")
            print(f"요청 데이터: {json.dumps(data, ensure_ascii=False)}")
            print(f"상태 코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if verbose:
                print("응답:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            return True, result
        else:
            if verbose:
                print(f"오류 응답: {response.text}")
            return False, response.text
    except Exception as e:
        if verbose:
            print(f"테스트 실패: {str(e)}")
        return False, str(e)
    finally:
        if verbose:
            print("==============================\n")


def test_health(verbose=True, url_base=BASE_URL):
    """건강 기반 식단 추천 API 테스트"""
    url = f"{url_base}/ai/health-recommendation/"
    data = {
        "weight": 70,
        "goal": "diet",
        "exercise_frequency": "two_to_three",
        "allergies": ["땅콩"],
        "disliked_foods": ["당근"],
    }

    try:
        response = requests.post(url, json=data)

        if verbose:
            print("\n===== 건강 기반 식단 추천 API 테스트 =====")
            print(f"요청 URL: {url}")
            print(f"요청 데이터: {json.dumps(data, ensure_ascii=False)}")
            print(f"상태 코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if verbose:
                print("응답:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            return True, result
        else:
            if verbose:
                print(f"오류 응답: {response.text}")
            return False, response.text
    except Exception as e:
        if verbose:
            print(f"테스트 실패: {str(e)}")
        return False, str(e)
    finally:
        if verbose:
            print("==============================\n")


def test_food(verbose=True, url_base=BASE_URL):
    """음식 추천 API 테스트"""
    url = f"{url_base}/ai/food-recommendation/"
    data = {
        "cuisine_type": "한식",
        "food_base": "밥",
        "taste": "매운맛",
        "dietary_type": "건강한 맛",
        "last_meal": "샐러드",
    }

    try:
        response = requests.post(url, json=data)

        if verbose:
            print("\n===== 음식 추천 API 테스트 =====")
            print(f"요청 URL: {url}")
            print(f"요청 데이터: {json.dumps(data, ensure_ascii=False)}")
            print(f"상태 코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if verbose:
                print("응답:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            return True, result
        else:
            if verbose:
                print(f"오류 응답: {response.text}")
            return False, response.text
    except Exception as e:
        if verbose:
            print(f"테스트 실패: {str(e)}")
        return False, str(e)
    finally:
        if verbose:
            print("==============================\n")


def test_invalid_ingredients(verbose=True, url_base=BASE_URL):
    """잘못된 식재료 테스트"""
    url = f"{url_base}/ai/recipe-recommendation/"
    data = {
        "ingredients": ["쌀", "김치", "컴퓨터", "자동차"],  # 잘못된 식재료 포함
        "serving_size": 2,
        "cooking_time": 30,
    }

    try:
        response = requests.post(url, json=data)

        if verbose:
            print("\n===== 잘못된 식재료 검증 테스트 =====")
            print(f"요청 URL: {url}")
            print(f"요청 데이터: {json.dumps(data, ensure_ascii=False)}")
            print(f"상태 코드: {response.status_code}")

        if response.status_code == 400:
            result = response.json()
            if verbose:
                print("응답:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            return True, result
        else:
            if verbose:
                print(f"예상치 못한 응답: {response.text}")
            return False, response.text
    except Exception as e:
        if verbose:
            print(f"테스트 실패: {str(e)}")
        return False, str(e)
    finally:
        if verbose:
            print("==============================\n")


def run_all_tests(url_base=BASE_URL):
    """모든 테스트를 실행"""
    successes = 0
    failures = 0

    print("==== AI 추천 API 전체 테스트 시작 ====\n")

    # 레시피 추천 테스트
    success, _ = test_recipe(True, url_base)
    if success:
        successes += 1
    else:
        failures += 1

    # 건강 추천 테스트
    success, _ = test_health(True, url_base)
    if success:
        successes += 1
    else:
        failures += 1

    # 음식 추천 테스트
    success, _ = test_food(True, url_base)
    if success:
        successes += 1
    else:
        failures += 1

    # 잘못된 식재료 테스트
    success, _ = test_invalid_ingredients(True, url_base)
    if success:
        successes += 1
    else:
        failures += 1

    print(f"\n==== 테스트 완료 ====")
    print(f"성공: {successes}")
    print(f"실패: {failures}")
    print("===================\n")

    return successes == 4  # 모든 테스트가 성공했는지 여부


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI 추천 API 테스트")
    parser.add_argument("--url", default=BASE_URL, help="API 서버 URL")
    parser.add_argument(
        "--test",
        choices=["recipe", "health", "food", "invalid", "all"],
        default="all",
        help="실행할 테스트 유형",
    )

    args = parser.parse_args()

    if args.test == "recipe":
        test_recipe(True, args.url)
    elif args.test == "health":
        test_health(True, args.url)
    elif args.test == "food":
        test_food(True, args.url)
    elif args.test == "invalid":
        test_invalid_ingredients(True, args.url)
    else:  # all
        success = run_all_tests(args.url)
        if not success:
            sys.exit(1)  # 테스트 실패 시 오류 코드 반환
