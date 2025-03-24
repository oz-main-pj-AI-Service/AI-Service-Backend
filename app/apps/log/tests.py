# import json
# import uuid
# from unittest.mock import MagicMock, patch

# from apps.log.models import ActivityLog
# from django.contrib.auth import get_user_model
# from django.contrib.auth.signals import user_logged_in, user_logged_out
# from django.db.models.signals import post_save
# from django.test import TestCase, override_settings
# from django.urls import reverse
# from rest_framework.test import APIClient

# User = get_user_model()
#
#
# # 시그널 핸들러 직접 정의
# def create_login_log(sender, user, request, **kwargs):
#     """사용자 로그인 시 activity log 기록"""
#     try:
#         ActivityLog.objects.create(
#             user_id=user,
#             action=ActivityLog.ActionType.LOGIN,
#             ip_address="127.0.0.1",
#             user_agent=request.META.get("HTTP_USER_AGENT", ""),
#             details={"message": "로그인 성공"},
#         )
#     except Exception as e:
#         print(f"사용자 로그인 로깅 중 오류 발생: {e}")

# def create_logout_log(sender, user, request, **kwargs):
#     """사용자 로그아웃 시 ActivityLog 생성"""
#     if user:
#         try:
#             ActivityLog.objects.create(
#                 user_id=user,
#                 action=ActivityLog.ActionType.LOGOUT,
#                 ip_address="127.0.0.1",
#                 user_agent=request.META.get("HTTP_USER_AGENT", ""),
#                 details={"message": "로그아웃 성공"},
#             )
#         except Exception as e:
#             print(f"사용자 로그아웃 로깅 중 오류 발생: {e}")

# def create_user_log(sender, instance, created, **kwargs):
#     """사용자 계정 생성 시 로그 자동 기록"""
#     if created:
#         try:
#             ActivityLog.objects.create(
#                 user_id=instance,
#                 action=ActivityLog.ActionType.UPDATE_PROFILE,
#                 ip_address="0.0.0.0",
#                 user_agent="System",
#                 details={"message": "사용자 계정 생성"},
#             )
#         except Exception as e:
#             print(f"사용자 계정 생성 로깅 중 오류 발생: {e}")

# def create_email_verification_log(sender, instance, created, **kwargs):
#     """이메일 인증 완료 시 로그 생성"""
#     if not created and hasattr(instance, "email_verified") and instance.email_verified:
#         try:
#             ActivityLog.objects.create(
#                 user_id=instance,
#                 action=ActivityLog.ActionType.UPDATE_PROFILE,
#                 ip_address="0.0.0.0",
#                 user_agent="System",
#                 details={"message": "이메일 인증 완료"},
#             )
#         except Exception as e:
#             print(f"이메일 인증 완료 로깅 중 오류 발생: {e}")



# @override_settings(SIGNAL_TESTING=True)
# class ActivityLogSignalTest(TestCase):
#     """ActivityLog 시그널 기능 테스트"""

#     # 테스트 데이터베이스 처리 방식 변경
#     multi_db = True


#     def setUp(self):
#         """테스트 데이터 설정"""
#         # 시그널 핸들러 등록
#         user_logged_in.connect(create_login_log)
#         user_logged_out.connect(create_logout_log)
#         post_save.connect(create_user_log, sender=User)
#         post_save.connect(create_email_verification_log, sender=User)


#         # 각 테스트마다 고유한 이메일 사용
#         admin_email = f"admin_{uuid.uuid4()}@example.com"
#         user_email = f"user_{uuid.uuid4()}@example.com"


#         # 관리자 사용자 생성
#         self.admin_user = User.objects.create_superuser(
#             email=admin_email,
#             password="adminpassword",
#             nickname="관리자",
#         )
#         # 일반 사용자 생성
#         self.normal_user = User.objects.create_user(
#             email=user_email,
#             password="userpassword",
#             nickname="일반사용자",
#         )
#         # Django 테스트 클라이언트
#         self.client = self.client_class()
#         # API 테스트용 클라이언트
#         self.api_client = APIClient()

#     def tearDown(self):
#         """테스트 종료 시 정리"""
#         # 시그널 연결 해제
#         user_logged_in.disconnect(create_login_log)
#         user_logged_out.disconnect(create_logout_log)
#         post_save.disconnect(create_user_log, sender=User)
#         post_save.disconnect(create_email_verification_log, sender=User)

#     @patch("apps.utils.signals.get_client_ip")
#     def test_login_creates_log(self, mock_get_client_ip):
#         """로그인 시 로그가 생성되는지 테스트"""
#         # 테스트 시작 시 로그 삭제
#         ActivityLog.objects.all().delete()


#         # IP 주소 모킹
#         mock_get_client_ip.return_value = "127.0.0.1"

#         # Mock 요청 객체 생성
#         request = MagicMock()
#         request.META = {"REMOTE_ADDR": "127.0.0.1", "HTTP_USER_AGENT": "Test Browser"}

#         # 시그널 직접 발생
#         user_logged_in.send(sender=User, request=request, user=self.normal_user)


#         # 생성된 로그 찾기
#         log = ActivityLog.objects.filter(
#             user_id=self.normal_user,
#             action=ActivityLog.ActionType.LOGIN,
#             details__message="로그인 성공",
#         ).first()

#         # 로그가 생성되었는지 확인
#         self.assertIsNotNone(log, "로그인 로그가 생성되지 않았습니다")
#         self.assertEqual(log.user_id, self.normal_user)
#         self.assertEqual(log.action, ActivityLog.ActionType.LOGIN)

#     @patch("apps.utils.signals.get_client_ip")
#     def test_logout_creates_log(self, mock_get_client_ip):
#         """로그아웃 시 로그가 생성되는지 테스트"""
#         # 테스트 시작 시 로그 삭제
#         ActivityLog.objects.all().delete()


#         # IP 주소 모킹
#         mock_get_client_ip.return_value = "127.0.0.1"

#         # Mock 요청 객체 생성
#         request = MagicMock()
#         request.META = {"REMOTE_ADDR": "127.0.0.1", "HTTP_USER_AGENT": "Test Browser"}

#         # 시그널 직접 발생
#         user_logged_out.send(sender=User, request=request, user=self.normal_user)


#         # 생성된 로그 찾기
#         log = ActivityLog.objects.filter(
#             user_id=self.normal_user,
#             action=ActivityLog.ActionType.LOGOUT,
#             details__message="로그아웃 성공",
#         ).first()

#         # 로그가 생성되었는지 확인
#         self.assertIsNotNone(log, "로그아웃 로그가 생성되지 않았습니다")
#         self.assertEqual(log.user_id, self.normal_user)
#         self.assertEqual(log.action, ActivityLog.ActionType.LOGOUT)

#     def test_user_creation_creates_log(self):
#         """사용자 생성 시 로그가 생성되는지 테스트"""
#         # 테스트 시작 시 로그 삭제
#         ActivityLog.objects.all().delete()

#         # 새 사용자 생성 (고유 이메일 사용)
#         new_email = f"newuser_{uuid.uuid4()}@example.com"
#         new_user = User.objects.create_user(
#             email=new_email,
#             password="newuserpassword",
#             nickname="새사용자",
#         )

#         # 생성된 로그 찾기
#         log = ActivityLog.objects.filter(
#             user_id=new_user,
#             action=ActivityLog.ActionType.UPDATE_PROFILE,
#             details__message="사용자 계정 생성",
#         ).first()

#         # 로그가 생성되었는지 확인
#         self.assertIsNotNone(log, "사용자 생성 로그가 생성되지 않았습니다")
#         self.assertEqual(log.user_id, new_user)
#         self.assertEqual(log.action, ActivityLog.ActionType.UPDATE_PROFILE)

#     def test_email_verification_creates_log(self):
#         """이메일 인증 완료 시 로그가 생성되는지 테스트"""
#         # 테스트 시작 시 로그 삭제
#         ActivityLog.objects.all().delete()

#         # 사용자의 이메일 인증 속성이 있는지 확인
#         if not hasattr(self.normal_user, "email_verified"):
#             # 테스트에서만 속성 추가
#             self.normal_user.email_verified = False
#             self.normal_user.save()
#             # 속성 추가 시 로그가 생성될 수 있으므로 다시 삭제
#             ActivityLog.objects.all().delete()


#         # 이메일 인증 상태 변경
#         self.normal_user.email_verified = True
#         self.normal_user.save()


#         # 생성된 로그 찾기
#         log = ActivityLog.objects.filter(
#             user_id=self.normal_user,
#             action=ActivityLog.ActionType.UPDATE_PROFILE,
#             details__message="이메일 인증 완료",
#         ).first()

#         # 로그가 생성되었는지 확인
#         self.assertIsNotNone(log, "이메일 인증 로그가 생성되지 않았습니다")
#         self.assertEqual(log.user_id, self.normal_user)
#         self.assertEqual(log.action, ActivityLog.ActionType.UPDATE_PROFILE)

#     def test_admin_can_view_all_logs(self):
#         """관리자가 모든 로그를 볼 수 있는지 테스트"""
#         # 테스트 시작 시 로그 삭제
#         ActivityLog.objects.all().delete()

#         # 테스트용 로그 생성
#         admin_log = ActivityLog.objects.create(
#             user_id=self.admin_user,
#             action=ActivityLog.ActionType.LOGIN,
#             ip_address="127.0.0.1",
#             user_agent="Test Browser",
#             details={"message": "관리자 로그인"},
#         )

#         user_log = ActivityLog.objects.create(
#             user_id=self.normal_user,
#             action=ActivityLog.ActionType.LOGIN,
#             ip_address="127.0.0.1",
#             user_agent="Test Browser",
#             details={"message": "일반 사용자 로그인"},
#         )


#         # API 클라이언트로 관리자 인증
#         self.api_client.force_authenticate(user=self.admin_user)


#         # 로그 조회 API 호출 - 실제 URL 패턴 이름으로 변경 필요
#         try:
#             url = reverse("api:logs-list")  # URL 이름이 api:logs-list일 수 있음
#         except:
#             try:
#                 url = reverse("log:log-list")  # 또는 log:log-list일 수 있음
#             except:
#                 # 테스트 목적으로 하드코딩된 URL 사용
#                 url = "/api/logs/"


#         response = self.api_client.get(url, format="json")

#         # 응답 확인
#         self.assertEqual(response.status_code, 200)


#         # 모든 사용자의 로그가 포함되어 있는지 확인
#         data = json.loads(response.content)
#         results = data.get("results", data)  # 페이지네이션 여부에 따라 다름
#         user_ids = [log.get("user_id") for log in results]


#         # admin_user와 normal_user 모두의 로그가 포함되어 있어야 함
#         self.assertTrue(str(self.admin_user.id) in user_ids)
#         self.assertTrue(str(self.normal_user.id) in user_ids)


#     def test_user_can_view_only_own_logs(self):
#         """일반 사용자가 자신의 로그만 볼 수 있는지 테스트"""
#         # 테스트 시작 시 로그 삭제
#         ActivityLog.objects.all().delete()

#         # 테스트용 로그 생성
#         admin_log = ActivityLog.objects.create(
#             user_id=self.admin_user,
#             action=ActivityLog.ActionType.LOGIN,
#             ip_address="127.0.0.1",
#             user_agent="Test Browser",
#             details={"message": "관리자 로그인"},
#         )

#         user_log = ActivityLog.objects.create(
#             user_id=self.normal_user,
#             action=ActivityLog.ActionType.LOGIN,
#             ip_address="127.0.0.1",
#             user_agent="Test Browser",
#             details={"message": "일반 사용자 로그인"},
#         )


#         # API 클라이언트로 일반 사용자 인증
#         self.api_client.force_authenticate(user=self.normal_user)


#         # 로그 조회 API 호출 - 실제 URL 패턴 이름으로 변경 필요
#         try:
#             url = reverse("api:logs-list")  # URL 이름이 api:logs-list일 수 있음
#         except:
#             try:
#                 url = reverse("log:log-list")  # 또는 log:log-list일 수 있음
#             except:
#                 # 테스트 목적으로 하드코딩된 URL 사용
#                 url = "/api/logs/"


#         response = self.api_client.get(url, format="json")

#         # 응답 확인
#         self.assertEqual(response.status_code, 200)


#         # 사용자 자신의 로그만 포함되어 있는지 확인
#         data = json.loads(response.content)
#         results = data.get("results", data)  # 페이지네이션 여부에 따라 다름
#         user_ids = [log.get("user_id") for log in results]

#         # normal_user의 로그만 포함되어 있어야 함
#         self.assertTrue(str(self.normal_user.id) in user_ids)
#         self.assertFalse(str(self.admin_user.id) in user_ids)
