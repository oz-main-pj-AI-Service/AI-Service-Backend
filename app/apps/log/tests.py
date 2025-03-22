# import json
# import uuid
#
# from apps.log.models import ActivityLog
# from apps.log.views import LogListCreateView
# from django.contrib.auth import get_user_model
# from django.test import RequestFactory, TestCase
# from django.urls import reverse
# from rest_framework import status
# from rest_framework.test import APIClient, APITestCase
#
# User = get_user_model()
#
#
# class ActivityLogSignalTests(TestCase):
#     """시그널 기능 테스트"""
#
#     def setUp(self):
#         self.user = User.objects.create_user(
#             email="test@example.com",
#             nickname="testuser",
#             password="testpassword123",
#             phone_number="01012345678",
#         )
#         self.user.email_verified = True
#         self.user.is_active = True
#         self.user.save()
#
#     def test_user_creation_signal(self):
#         """사용자 생성 시 로그 자동 생성 테스트"""
#         # 테스트용 사용자 생성
#         new_user = User.objects.create_user(
#             email="testsignal@example.com",
#             nickname="testsignal",
#             password="testpassword123",
#             phone_number="01012345679",
#         )
#
#         # 로그가 생성되었는지 확인
#         logs = ActivityLog.objects.filter(user_id=new_user)
#         self.assertEqual(logs.count(), 1)
#         self.assertEqual(logs.first().action, ActivityLog.ActionType.UPDATE_PROFILE)
#         self.assertEqual(logs.first().details.get("message"), "사용자 계정 생성")
#
#     def test_email_verification_signal(self):
#         """이메일 인증 완료 시 로그 생성 테스트"""
#         # 이메일 미인증 사용자 생성
#         user = User.objects.create_user(
#             email="unverified@example.com",
#             nickname="unverified",
#             password="testpassword123",
#             phone_number="01012345680",
#         )
#
#         # 초기 로그 카운트 확인 (사용자 생성 로그 1개)
#         initial_logs_count = ActivityLog.objects.filter(user_id=user).count()
#
#         # 이메일 인증 완료 처리
#         user.email_verified = True
#         user.save()
#
#         # 로그가 추가되었는지 확인
#         new_logs_count = ActivityLog.objects.filter(user_id=user).count()
#         self.assertEqual(new_logs_count, initial_logs_count + 1)
#
#         # 이메일 인증 관련 로그 확인
#         log = ActivityLog.objects.filter(
#             user_id=user, details__message="이메일 인증 완료"
#         ).first()
#         self.assertIsNotNone(log)
#
#     def test_custom_activity_logged_signal(self):
#         """커스텀 activity_logged 시그널 테스트"""
#
#         # 로그인 전 시도 횟수 설정
#         self.user.login_attempts = 3
#         self.user.save()
#
#         # 가상의 로그 객체 생성
#         log = ActivityLog.objects.create(
#             user_id=self.user,
#             action=ActivityLog.ActionType.LOGIN,
#             ip_address="127.0.0.1",
#             user_agent="Test Browser",
#         )
#
#         # 시그널 수동 발생
#         activity_logged.send(
#             sender=self.__class__,
#             user=self.user,
#             action=ActivityLog.ActionType.LOGIN,
#             log_instance=log,
#         )
#
#         # 사용자 다시 불러오기
#         self.user.refresh_from_db()
#
#         # 로그인 시도 횟수가 리셋되었는지 확인
#         self.assertEqual(self.user.login_attempts, 0)
#
#
# class ActivityLogAPITests(APITestCase):
#     """API 엔드포인트 테스트"""
#
#     def setUp(self):
#         # 일반 사용자
#         self.user = User.objects.create_user(
#             email="user@example.com",
#             nickname="regularuser",
#             password="userpassword123",
#             phone_number="01012345678",
#         )
#         self.user.email_verified = True
#         self.user.is_active = True
#         self.user.save()
#
#         # 관리자 사용자
#         self.admin = User.objects.create_superuser(
#             email="admin@example.com",
#             nickname="adminuser",
#             password="adminpassword123",
#             phone_number="01098765432",
#         )
#
#         # 사용자 로그 생성
#         self.user_log = ActivityLog.objects.create(
#             user_id=self.user,
#             action=ActivityLog.ActionType.LOGIN,
#             ip_address="192.168.1.1",
#             user_agent="Test Browser",
#             details={"source": "web"},
#         )
#
#         # 관리자 로그 생성
#         self.admin_log = ActivityLog.objects.create(
#             user_id=self.admin,
#             action=ActivityLog.ActionType.LOGIN,
#             ip_address="192.168.1.2",
#             user_agent="Admin Browser",
#             details={"source": "admin-portal"},
#         )
#
#         self.client = APIClient()
#         self.log_list_url = reverse("log:log-list-create")
#         self.admin_log_list_url = reverse("log:admin-log-list-create")
#         self.user_log_detail_url = reverse(
#             "log:log-list-create", args=[self.user_log.id]
#         )
#         self.admin_log_detail_url = reverse(
#             "log:admin-log-list-create", args=[self.admin_log.id]
#         )
#
#     def test_log_list_admin(self):
#         """관리자는 모든 로그를 볼 수 있음"""
#         self.client.force_authenticate(user=self.admin)
#         response = self.client.get(self.log_list_url)
#
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         data = response.json()
#         self.assertGreaterEqual(data["count"], 2)  # 모든 로그 조회 가능
#
#         log_ids = [log["id"] for log in data["results"]]
#         self.assertIn(str(self.user_log.id), log_ids)
#         self.assertIn(str(self.admin_log.id), log_ids)
#
#     def test_admin_log_list_regular_user(self):
#         """일반 사용자는 관리자 로그 엔드포인트에 접근할 수 없음"""
#         self.client.force_authenticate(user=self.user)
#         response = self.client.get(self.admin_log_list_url)
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
#
#     def test_admin_log_list_admin(self):
#         """관리자는 관리자 로그 엔드포인트에 접근할 수 있음"""
#         self.client.force_authenticate(user=self.admin)
#         response = self.client.get(self.admin_log_list_url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     def test_create_log(self):
#         """로그 생성 테스트"""
#         self.client.force_authenticate(user=self.user)
#         log_data = {
#             "action": ActivityLog.ActionType.VIEW_REPORT,
#             "details": {"report_id": "123456"},
#         }
#
#         response = self.client.post(self.log_list_url, log_data, format="json")
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#
#         # 생성된 로그 확인
#         created_log = ActivityLog.objects.filter(
#             action=ActivityLog.ActionType.VIEW_REPORT
#         ).first()
#         self.assertIsNotNone(created_log)
#         self.assertEqual(created_log.user_id, self.user)
#         self.assertEqual(created_log.details.get("report_id"), "123456")
#
#     def test_filter_by_action(self):
#         """액션 타입으로 로그 필터링 테스트"""
#         # 기존 로그와 다른 액션의 로그 추가
#         ActivityLog.objects.create(
#             user_id=self.user,
#             action=ActivityLog.ActionType.LOGOUT,
#             ip_address="192.168.1.1",
#             user_agent="Test Browser",
#         )
#
#         self.client.force_authenticate(user=self.user)
#         response = self.client.get(
#             f"{self.log_list_url}?action={ActivityLog.ActionType.LOGIN}"
#         )
#
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         data = response.json()
#         self.assertEqual(data["count"], 1)
#         self.assertEqual(data["results"][0]["action"], ActivityLog.ActionType.LOGIN)
#
#
# class ActivityLogModelTests(TestCase):
#     """ActivityLog 모델 메서드 테스트"""
#
#     def setUp(self):
#         self.user = User.objects.create_user(
#             email="model_test@example.com",
#             nickname="modeltest",
#             password="testpassword123",
#             phone_number="01012345678",
#         )
#
#         # 로그 여러 개 생성
#         self.logs = []
#         for action in [
#             ActivityLog.ActionType.LOGIN,
#             ActivityLog.ActionType.LOGOUT,
#             ActivityLog.ActionType.VIEW_REPORT,
#         ]:
#             log = ActivityLog.objects.create(
#                 user_id=self.user,
#                 action=action,
#                 ip_address="192.168.1.1",
#                 user_agent="Test Browser",
#             )
#             self.logs.append(log)
#
#     def test_to_dict_method(self):
#         """to_dict 메서드 테스트"""
#         log_dict = self.logs[0].to_dict()
#
#         self.assertEqual(log_dict["id"], str(self.logs[0].id))
#         self.assertEqual(log_dict["user_id"], str(self.user.id))
#         self.assertEqual(log_dict["action"], self.logs[0].action)
#         self.assertEqual(log_dict["ip_address"], self.logs[0].ip_address)
#         self.assertEqual(log_dict["user_agent"], self.logs[0].user_agent)
#         self.assertIn("created_at", log_dict)
#         self.assertEqual(log_dict["details"], {})
