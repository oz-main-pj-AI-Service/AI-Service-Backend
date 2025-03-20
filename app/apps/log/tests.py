import json
import uuid
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.log.models import ActivityLog
from unittest.mock import patch

User = get_user_model()


class ActivityLogSignalTest(TestCase):
    """ActivityLog 시그널 기능 테스트"""
    
    # 테스트 데이터베이스 처리 방식 변경
    multi_db = True
    
    def setUp(self):
        """테스트 데이터 설정"""
        # 각 테스트마다 고유한 이메일 사용
        admin_email = f"admin_{uuid.uuid4()}@example.com"
        user_email = f"user_{uuid.uuid4()}@example.com"
        
        # 관리자 사용자 생성
        self.admin_user = User.objects.create_superuser(
            email=admin_email,
            password="adminpassword",
            nickname="관리자",
        )
        # 일반 사용자 생성
        self.normal_user = User.objects.create_user(
            email=user_email, 
            password="userpassword",
            nickname="일반사용자",
        )
        # Django 테스트 클라이언트
        self.client = self.client_class()
        # API 테스트용 클라이언트
        self.api_client = APIClient()

    @patch('apps.utils.signals.get_client_ip')
    def test_login_creates_log(self, mock_get_client_ip):
        """로그인 시 로그가 생성되는지 테스트"""
        # IP 주소 모킹
        mock_get_client_ip.return_value = "127.0.0.1"
        
        # 초기 로그 개수 확인
        initial_log_count = ActivityLog.objects.count()
        
        # 로그인 수행
        login_success = self.client.login(email=self.normal_user.email, password="userpassword")
        self.assertTrue(login_success)
        
        # 로그 생성 확인
        self.assertEqual(ActivityLog.objects.count(), initial_log_count + 1)
        
        # 로그 내용 확인
        log = ActivityLog.objects.latest("created_at")
        self.assertEqual(log.user_id, self.normal_user)
        self.assertEqual(log.action, ActivityLog.ActionType.LOGIN)
        self.assertEqual(log.details.get("message"), "로그인 성공")

    @patch('apps.utils.signals.get_client_ip')
    def test_logout_creates_log(self, mock_get_client_ip):
        """로그아웃 시 로그가 생성되는지 테스트"""
        # IP 주소 모킹
        mock_get_client_ip.return_value = "127.0.0.1"
        
        # 먼저 로그인
        self.client.login(email=self.normal_user.email, password="userpassword")
        
        # 현재 로그 개수 확인 (로그인 로그 1개가 생성된 상태)
        current_log_count = ActivityLog.objects.count()
        
        # 로그아웃 수행
        self.client.logout()
        
        # 로그 생성 확인
        self.assertEqual(ActivityLog.objects.count(), current_log_count + 1)
        
        # 로그 내용 확인
        log = ActivityLog.objects.latest("created_at")
        self.assertEqual(log.user_id, self.normal_user)
        self.assertEqual(log.action, ActivityLog.ActionType.LOGOUT)
        self.assertEqual(log.details.get("message"), "로그아웃 성공")

    @patch('apps.utils.signals.get_client_ip')
    def test_user_creation_creates_log(self, mock_get_client_ip):
        """사용자 생성 시 로그가 생성되는지 테스트"""
        # IP 주소 모킹
        mock_get_client_ip.return_value = "127.0.0.1"
        
        # 초기 로그 개수 확인
        initial_log_count = ActivityLog.objects.count()
        
        # 새 사용자 생성 (고유 이메일 사용)
        new_email = f"newuser_{uuid.uuid4()}@example.com"
        new_user = User.objects.create_user(
            email=new_email,
            password="newuserpassword",
            nickname="새사용자",
        )
        
        # 로그 생성 확인
        self.assertEqual(ActivityLog.objects.count(), initial_log_count + 1)
        
        # 로그 내용 확인
        log = ActivityLog.objects.filter(user_id=new_user).latest("created_at")
        self.assertEqual(log.action, ActivityLog.ActionType.UPDATE_PROFILE)
        self.assertEqual(log.details.get("message"), "사용자 계정 생성")

    @patch('apps.utils.signals.get_client_ip')
    def test_email_verification_creates_log(self, mock_get_client_ip):
        """이메일 인증 완료 시 로그가 생성되는지 테스트"""
        # IP 주소 모킹
        mock_get_client_ip.return_value = "127.0.0.1"
        
        # 사용자의 이메일 인증 속성이 있는지 확인
        if not hasattr(self.normal_user, 'email_verified'):
            # 테스트에서만 속성 추가
            self.normal_user.email_verified = False
            self.normal_user.save()
            
        # 초기 로그 개수 확인
        initial_log_count = ActivityLog.objects.count()
        
        # 이메일 인증 상태 변경
        self.normal_user.email_verified = True
        self.normal_user.save()
        
        # 로그 생성 확인
        self.assertEqual(ActivityLog.objects.count(), initial_log_count + 1)
        
        # 로그 내용 확인
        log = ActivityLog.objects.filter(user_id=self.normal_user).latest("created_at")
        self.assertEqual(log.action, ActivityLog.ActionType.UPDATE_PROFILE)
        self.assertEqual(log.details.get("message"), "이메일 인증 완료")

    @patch('apps.utils.signals.get_client_ip')
    def test_admin_can_view_all_logs(self, mock_get_client_ip):
        """관리자가 모든 로그를 볼 수 있는지 테스트"""
        # IP 주소 모킹
        mock_get_client_ip.return_value = "127.0.0.1"
        
        # 로그인 및 로그아웃해서 두 사용자에 대한 로그 생성
        self.client.login(email=self.normal_user.email, password="userpassword")
        self.client.logout()
        self.client.login(email=self.admin_user.email, password="adminpassword")
        self.client.logout()
        
        # API 클라이언트로 관리자 인증
        self.api_client.force_authenticate(user=self.admin_user)
        
        # 로그 조회 API 호출 - 실제 URL 패턴 이름으로 변경 필요
        try:
            url = reverse("api:logs-list")  # URL 이름이 api:logs-list일 수 있음
        except:
            try:
                url = reverse("log:log-list")  # 또는 log:log-list일 수 있음
            except:
                # 테스트 목적으로 하드코딩된 URL 사용
                url = "/api/logs/"
        
        response = self.api_client.get(url, format="json")
        
        # 응답 확인
        self.assertEqual(response.status_code, 200)
        
        # 모든 사용자의 로그가 포함되어 있는지 확인
        data = json.loads(response.content)
        results = data.get("results", data)  # 페이지네이션 여부에 따라 다름
        user_ids = [log.get("user_id") for log in results]
        
        # admin_user와 normal_user 모두의 로그가 포함되어 있어야 함
        self.assertTrue(str(self.admin_user.id) in user_ids)
        self.assertTrue(str(self.normal_user.id) in user_ids)

    @patch('apps.utils.signals.get_client_ip')
    def test_user_can_view_only_own_logs(self, mock_get_client_ip):
        """일반 사용자가 자신의 로그만 볼 수 있는지 테스트"""
        # IP 주소 모킹
        mock_get_client_ip.return_value = "127.0.0.1"
        
        # 로그인 및 로그아웃해서 두 사용자에 대한 로그 생성
        self.client.login(email=self.normal_user.email, password="userpassword")
        self.client.logout()
        self.client.login(email=self.admin_user.email, password="adminpassword")
        self.client.logout()
        
        # API 클라이언트로 일반 사용자 인증
        self.api_client.force_authenticate(user=self.normal_user)
        
        # 로그 조회 API 호출 - 실제 URL 패턴 이름으로 변경 필요
        try:
            url = reverse("api:logs-list")  # URL 이름이 api:logs-list일 수 있음
        except:
            try:
                url = reverse("log:log-list")  # 또는 log:log-list일 수 있음
            except:
                # 테스트 목적으로 하드코딩된 URL 사용
                url = "/api/logs/"
        
        response = self.api_client.get(url, format="json")
        
        # 응답 확인
        self.assertEqual(response.status_code, 200)
        
        # 사용자 자신의 로그만 포함되어 있는지 확인
        data = json.loads(response.content)
        results = data.get("results", data)  # 페이지네이션 여부에 따라 다름
        user_ids = [log.get("user_id") for log in results]
        
        # normal_user의 로그만 포함되어 있어야 함
        self.assertTrue(str(self.normal_user.id) in user_ids)
        self.assertFalse(str(self.admin_user.id) in user_ids)