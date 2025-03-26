def recipe_prompt(validated_data):
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
    """
