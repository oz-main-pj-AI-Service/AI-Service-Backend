def recipe_prompt(validated_data):
    return f"""
            다음 재료를 사용해서 요리 레시피를 만들어주세요:
            재료: {', '.join(validated_data['ingredients'])}
            몇인분: {validated_data['serving_size']}
            소요 시간: {validated_data['cooking_time']}분
            난이도: {validated_data['difficulty']}

            다음 형식으로 반환해주세요:
            {{
                "name": "요리이름",
                "description": "간단한 요리 설명",
                "cuisine_type": "요리 종류(한식/중식 등)",
                "meal_type": "식사 종류(아침/점심/저녁)",
                "preparation_time": 준비시간(분),
                "cooking_time": 조리시간(분),
                "serving_size": 제공인원,
                "difficulty": "{validated_data['difficulty']}",
                "ingredients": [
                    {{"name": "재료1", "amount": "양"}},
                    {{"name": "재료2", "amount": "양"}}
                ],
                "instructions": [
                    {{"step": 1, "description": "조리 단계 설명"}},
                    {{"step": 2, "description": "조리 단계 설명"}}
                ],
                "nutrition_info": {{
                    "calories": 칼로리,
                    "protein": 단백질(g),
                    "carbs": 탄수화물(g),
                    "fat": 지방(g)
                }}
            }}

            JSON 형식으로만 반환해주세요. 다른 텍스트나 설명은 포함하지 마세요.
            """


def stream_recipe_prompt(validated_data):
    return f"""
            다음 재료를 사용해서 요리 레시피를 만들어주세요. 자세하고 맛있게 설명해주세요:
            재료: {', '.join(validated_data['ingredients'])}
            몇인분: {validated_data['serving_size']}
            소요 시간: {validated_data['cooking_time']}분
            난이도: {validated_data['difficulty']}
        
            먼저 자연스러운 대화형으로 레시피를 설명해주세요. 
            그 후에 다음 형식으로 레시피 정보를 JSON 형식으로 제공해주세요:
        
            ###JSON###
            {{
                "name": "요리이름",
                "description": "간단한 요리 설명",
                "cuisine_type": "요리 종류(한식/중식 등)",
                "meal_type": "식사 종류(아침/점심/저녁)",
                "preparation_time": 준비시간(분),
                "cooking_time": 조리시간(분),
                "serving_size": 제공인원,
                "difficulty": "{validated_data['difficulty']}",
                "ingredients": [
                    {{"name": "재료1", "amount": "양"}},
                    {{"name": "재료2", "amount": "양"}}
                ],
                "instructions": [
                    {{"step": 1, "description": "조리 단계 설명"}},
                    {{"step": 2, "description": "조리 단계 설명"}}
                ],
                "nutrition_info": {{
                    "calories": 칼로리,
                    "protein": 단백질(g),
                    "carbs": 탄수화물(g),
                    "fat": 지방(g)
                }}
            }}
            JSON 형식으로 제공해 준다는 말 하지
            """


def stream_health_prompt(validated_data, allergies, disliked_foods):
    return f"""
                다음 정보를 바탕으로 건강한 식단을 추천해주세요:
                체중: {validated_data['weight']}kg
                목표: {validated_data['goal']} (벌크업/다이어트/유지)
                운동 빈도: {validated_data['exercise_frequency']} (주1회/주2~3회/주4~5회/운동안함)
                알레르기: {', '.join(allergies) if allergies else '없음'}
                비선호 음식: {', '.join(disliked_foods) if disliked_foods else '없음'}

                먼저 자연스러운 대화형으로 하루 식단 추천을 해주세요.
                그 후에 다음 형식으로 추천 정보를 JSON 형식으로 제공해주세요:

                ###JSON###
                {{
                    "daily_calorie_target": 하루 권장 칼로리,
                    "protein_target": 하루 단백질 목표(g),
                    "meals": [
                        {{
                            "type": "아침",
                            "food_name": "음식명",
                            "food_type": "음식 종류",
                            "description": "설명",
                            "nutritional_info": {{
                                "calories": 칼로리,
                                "protein": 단백질(g),
                                "carbs": 탄수화물(g),
                                "fat": 지방(g)
                            }}
                        }},
                        {{
                            "type": "점심",
                            "food_name": "음식명",
                            "food_type": "음식 종류",
                            "description": "설명",
                            "nutritional_info": {{
                                "calories": 칼로리,
                                "protein": 단백질(g),
                                "carbs": 탄수화물(g),
                                "fat": 지방(g)
                            }}
                        }},
                        {{
                            "type": "저녁",
                            "food_name": "음식명",
                            "food_type": "음식 종류",
                            "description": "설명",
                            "nutritional_info": {{
                                "calories": 칼로리,
                                "protein": 단백질(g),
                                "carbs": 탄수화물(g),
                                "fat": 지방(g)
                            }}
                        }}
                    ],
                    "recommendation_reason": "추천 이유 및 설명"
                }}
                JSON 형식으로 제공해 준다는 말 하지마
                """


def health_prompt(validated_data, allergies, disliked_foods):
    return f"""
            다음 정보를 바탕으로 건강한 식단을 추천해주세요:
            체중: {validated_data['weight']}kg
            목표: {validated_data['goal']} (벌크업/다이어트/유지)
            운동 빈도: {validated_data['exercise_frequency']} (주1회/주2~3회/주4~5회/운동안함)
            알레르기: {', '.join(allergies) if allergies else '없음'}
            비선호 음식: {', '.join(disliked_foods) if disliked_foods else '없음'}

            하루 3끼 식단(아침, 점심, 저녁)을 추천해주세요. 

            다음 JSON 형식으로 반환해주세요:
            {{
                "daily_calorie_target": 하루 권장 칼로리,
                "protein_target": 하루 단백질 목표(g),
                "meals": [
                    {{
                        "type": "아침",
                        "food_name": "음식명",
                        "food_type": "음식 종류",
                        "description": "설명",
                        "nutritional_info": {{
                            "calories": 칼로리,
                            "protein": 단백질(g),
                            "carbs": 탄수화물(g),
                            "fat": 지방(g)
                        }}
                    }},
                    {{
                        "type": "점심",
                        "food_name": "음식명",
                        "food_type": "음식 종류",
                        "description": "설명",
                        "nutritional_info": {{
                            "calories": 칼로리,
                            "protein": 단백질(g),
                            "carbs": 탄수화물(g),
                            "fat": 지방(g)
                        }}
                    }},
                    {{
                        "type": "저녁",
                        "food_name": "음식명",
                        "food_type": "음식 종류",
                        "description": "설명",
                        "nutritional_info": {{
                            "calories": 칼로리,
                            "protein": 단백질(g),
                            "carbs": 탄수화물(g),
                            "fat": 지방(g)
                        }}
                    }}
                ],
                "recommendation_reason": "추천 이유 및 설명"
            }}

            JSON 형식으로만 반환해주세요. 다른 텍스트나 설명은 포함하지 마세요.
            """


def stream_food_prompt(cuisine_type, food_base, taste, dietary_type, last_meal):
    return f"""
            다음 조건에 맞는 음식을 추천해주세요:
            음식 종류: {cuisine_type if cuisine_type else '특별한 선호 없음'} (한식/중식/일식/양식/동남아)
            음식 기반: {food_base if food_base else '특별한 선호 없음'} (면/밥/빵)
            맛 선호도: {taste if taste else '특별한 선호 없음'} (단맛/고소한맛/매운맛/상큼한맛)
            식단 유형: {dietary_type if dietary_type else '특별한 선호 없음'} (자극적/건강한 맛)
            최근 식사: {last_meal if last_meal else '정보 없음'}

            먼저 자연스러운 대화형으로 음식 추천을 해주세요. 이유와 함께 설명해주세요.
            그 후에 다음 형식으로 추천 정보를 JSON 형식으로 제공해주세요 (1개만):

            ###JSON###
            {{
                "recommendation": {{
                    "food_name": "음식명",
                    "food_type": "음식 종류",
                    "description": "음식 설명",
                    "nutritional_info": {{
                        "calories": 칼로리,
                        "protein": 단백질(g),
                        "carbs": 탄수화물(g),
                        "fat": 지방(g)
                    }},
                    "recommendation_reason": "추천 이유"
                }}
            }}
            JSON 형식으로 제공해 준다는 말 하지
            """


def food_prompt(cuisine_type, food_base, taste, dietary_type, last_meal):
    return f"""
            다음 조건에 맞는 음식을 추천해주세요:
            음식 종류: {cuisine_type if cuisine_type else '특별한 선호 없음'} (한식/중식/일식/양식/동남아)
            음식 기반: {food_base if food_base else '특별한 선호 없음'} (면/밥/빵)
            맛 선호도: {taste if taste else '특별한 선호 없음'} (단맛/고소한맛/매운맛/상큼한맛)
            식단 유형: {dietary_type if dietary_type else '특별한 선호 없음'} (자극적/건강한 맛)
            최근 식사: {last_meal if last_meal else '정보 없음'}

            다음 JSON 형식으로 1가지 추천 음식을 반환해주세요:
            {{
                "recommendation": {{
                    "food_name": "음식명",
                    "food_type": "음식 종류",
                    "description": "음식 설명",
                    "nutritional_info": {{
                        "calories": 칼로리,
                        "protein": 단백질(g),
                        "carbs": 탄수화물(g),
                        "fat": 지방(g)
                    }},
                    "recommendation_reason": "추천 이유"
                }}
            }}

            JSON 형식으로만 반환해주세요. 다른 텍스트나 설명은 포함하지 마세요.
            """
