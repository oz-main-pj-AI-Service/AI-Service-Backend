import uuid

from apps.log.models import ActivityLog
from django.contrib.auth import get_user_model
from django.db import models
from django.test import TestCase
from django.utils import timezone

User = get_user_model()


class ActivityLogModelTest(TestCase):
    """ActivityLog 모델 테스트 클래스"""

    def setUp(self):
        """테스트에 필요한 데이터 설정"""
        # 테스트용 사용자 생성
        self.user = User.objects.create_user(
            email="existing@example.com",
            nickname="test",
            password="test1234",
            phone_number="1234",
        )

        # 익명 로그를 위한 데이터
        self.ip_address = "192.168.1.1"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

        # 기본 액션 유형
        self.login_action = ActivityLog.ActionType.LOGIN
        self.logout_action = ActivityLog.ActionType.LOGOUT
        self.update_profile_action = ActivityLog.ActionType.UPDATE_PROFILE
        self.view_report_action = ActivityLog.ActionType.VIEW_REPORT

        # 추가 정보
        self.login_details = {"device": "desktop", "location": "home"}

    def test_create_activity_log(self):
        """ActivityLog 생성 테스트"""
        # 사용자 로그인 로그 생성
        login_log = ActivityLog.objects.create(
            user_id=self.user,
            action=self.login_action,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            details=self.login_details,
        )

        # 데이터베이스에서 조회
        saved_log = ActivityLog.objects.get(id=login_log.id)

        # 기본 필드 검증
        self.assertEqual(saved_log.user_id, self.user)
        self.assertEqual(saved_log.action, self.login_action)
        self.assertEqual(saved_log.ip_address, self.ip_address)
        self.assertEqual(saved_log.user_agent, self.user_agent)
        self.assertEqual(saved_log.details, self.login_details)
        self.assertIsNotNone(saved_log.created_at)

        # UUID 형식 검증
        self.assertIsInstance(saved_log.id, uuid.UUID)

    def test_create_anonymous_log(self):
        """익명 사용자 로그 생성 테스트"""
        # 익명 사용자 로그 생성
        anon_log = ActivityLog.objects.create(
            user_id=None,
            action=self.view_report_action,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

        # 데이터베이스에서 조회
        saved_log = ActivityLog.objects.get(id=anon_log.id)

        # 익명 사용자 검증
        self.assertIsNone(saved_log.user_id)
        self.assertEqual(saved_log.action, self.view_report_action)

        # __str__ 메서드 검증
        self.assertIn("Anonymous", str(saved_log))

    def test_activity_log_ordering(self):
        """기본 정렬 순서(생성일 내림차순) 테스트"""
        # 첫 번째 로그 생성
        first_log = ActivityLog.objects.create(
            user_id=self.user,
            action=self.login_action,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

        # 잠시 대기 후 두 번째 로그 생성
        import time

        time.sleep(0.1)  # 100ms 대기

        second_log = ActivityLog.objects.create(
            user_id=self.user,
            action=self.logout_action,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

        # 모든 로그 조회 (기본 정렬 순서 적용)
        logs = list(ActivityLog.objects.all())

        # 최신 로그가 먼저 나와야 함
        self.assertEqual(logs[0], second_log)
        self.assertEqual(logs[1], first_log)

    def test_to_dict_method(self):
        """to_dict 메서드 테스트"""
        # 로그 생성
        log = ActivityLog.objects.create(
            user_id=self.user,
            action=self.update_profile_action,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            details={"field": "profile_picture"},
        )

        # to_dict 메서드 호출
        log_dict = log.to_dict()

        # 딕셔너리 형태 검증
        self.assertEqual(log_dict["id"], str(log.id))
        self.assertEqual(log_dict["user_id"], str(self.user.id))
        self.assertEqual(log_dict["action"], self.update_profile_action)
        self.assertEqual(log_dict["ip_address"], self.ip_address)
        self.assertEqual(log_dict["user_agent"], self.user_agent)
        self.assertEqual(log_dict["details"], {"field": "profile_picture"})
        self.assertIsInstance(log_dict["created_at"], str)  # ISO 형식 문자열 확인

    def test_get_user_log_count(self):
        """사용자 로그 수 조회 메서드 테스트"""
        # 로그 여러 개 생성
        ActivityLog.objects.create(
            user_id=self.user,
            action=self.login_action,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

        ActivityLog.objects.create(
            user_id=self.user,
            action=self.update_profile_action,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

        ActivityLog.objects.create(
            user_id=self.user,
            action=self.view_report_action,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

        # 다른 사용자 로그 생성
        other_user = User.objects.create_user(
            email="existing2@example.com",
            nickname="test",
            password="test1234",
            phone_number="1232",
        )

        ActivityLog.objects.create(
            user_id=other_user,
            action=self.login_action,
            ip_address="192.168.1.2",
            user_agent=self.user_agent,
        )

        # 첫 번째 사용자의 로그 수 검증
        log_count = ActivityLog.get_user_log_count(self.user.id)
        self.assertEqual(log_count, 3)

        # 두 번째 사용자의 로그 수 검증
        other_log_count = ActivityLog.get_user_log_count(other_user.id)
        self.assertEqual(other_log_count, 1)
