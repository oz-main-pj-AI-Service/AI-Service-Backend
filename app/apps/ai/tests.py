import json
import uuid

from apps.ai.models import AiRequest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

User = get_user_model()


class AiRequestModelTest(TestCase):
    def setUp(self):
        # 테스트용 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="testpassword"
        )

        self.request_type = "TEXT_GENERATION"
        self.request_data = {"prompt": "야이미친놈아", "max_tokens": 500}
        self.response_data = {"text": "왜 ㅅㅂ", "tokens_used": 100}

    def test_create_ai_request(self):
        ai_request = AiRequest.objects.create(
            user_id=self.user,
            request_type=self.request_type,
            request_data=self.request_data,
        )
        saved_request = AiRequest.objects.get(id=ai_request.id)

        self.assertEqual(saved_request.user_id, self.user)
        self.assertEqual(saved_request.request_type, self.request_type)
        self.assertEqual(saved_request.request_data, self.request_data)
        self.assertIsNone(saved_request.response_data)
        self.assertIsNotNone(saved_request.created_at)
        self.assertIsInstance(saved_request.id, uuid.UUID)

    # 응답 데이터가 포함된 요청 생성 테스트
    def test_ai_request_with_response(self):
        ai_request = AiRequest.objects.create(
            user_id=self.user,
            request_type=self.request_type,
            request_data=self.request_data,
            response_data=self.response_data,
        )
        saved_request = AiRequest.objects.get(id=ai_request.id)
        self.assertEqual(saved_request.response_data, self.response_data)

    # 메서드 테스트
    def test_ai_request_str_method(self):
        ai_request = AiRequest.objects.create(
            user_id=self.user,
            request_type=self.request_type,
            request_data=self.request_data,
        )
        expected_str = f"{self.request_type} - {ai_request.created_at}"
        self.assertEqual(str(ai_request), expected_str)

    # 최신화 정렬 테스트
    def test_ai_request_ordering(self):
        # 첫 번째 요청 생성
        first_request = AiRequest.objects.create(
            user_id=self.user,
            request_type=self.request_type,
            request_data=self.request_data,
        )

        # 두 번째 요청 생성 (시간차 공격)
        import time

        time.sleep(0.1)  # 100ms 대기

        second_request = AiRequest.objects.create(
            user_id=self.user,
            request_type="SUMMARIZATION",
            request_data={"text": "요약할 텍스트..."},
        )

        # 모든 요청 조회 (기본 정렬 순서 적용)
        requests = list(AiRequest.objects.all())

        # 최신 요청이 먼저 나와야 함
        self.assertEqual(requests[0], second_request)
        self.assertEqual(requests[1], first_request)

    # 필드 유효성 검사
    def test_json_field_validation(self):
        # 유효한 JSON 데이터
        valid_json = {"key": "value", "nested": {"inner": "data"}}

        ai_request = AiRequest.objects.create(
            user_id=self.user, request_type=self.request_type, request_data=valid_json
        )

        saved_request = AiRequest.objects.get(id=ai_request.id)
        self.assertEqual(saved_request.request_data, valid_json)

        # 복잡한 JSON 구조 테스트
        complex_json = {
            "array": [1, 2, 3, 4],
            "boolean": True,
            "null": None,
            "number": 123.456,
            "nested": {"a": "b", "c": ["d", "e", "f"]},
        }

        ai_request.request_data = complex_json
        ai_request.save()

        saved_request = AiRequest.objects.get(id=ai_request.id)
        self.assertEqual(saved_request.request_data, complex_json)

    def test_delete_user_cascades(self):
        """사용자 삭제 시 요청도 삭제되는지 테스트 (CASCADE)"""
        # 요청 생성
        ai_request = AiRequest.objects.create(
            user_id=self.user,
            request_type=self.request_type,
            request_data=self.request_data,
        )

        request_id = ai_request.id

        # 사용자 삭제
        self.user.delete()

        # 연결된 요청도 삭제되었는지 확인
        with self.assertRaises(AiRequest.DoesNotExist):
            AiRequest.objects.get(id=request_id)
