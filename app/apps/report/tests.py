import uuid

from apps.report.models import Report
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class ReportAPITests(APITestCase):
    """리포트 API 테스트 클래스"""

    def setUp(self):
        """테스트 설정"""
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="testpassword"
        )

        # 다른 테스트 사용자 생성 (권한 테스트용)
        self.other_user = User.objects.create_user(
            email="other@example.com", password="otherpassword"
        )

        # 인증 설정
        self.client.force_authenticate(user=self.user)

        # 테스트 리포트 생성
        self.report = Report.objects.create(
            user_id=self.user,
            title="테스트 리포트",
            description="테스트 설명",
            type=Report.ReportType.ERROR,
            status=Report.StatusType.OPEN,
        )

        # 다른 사용자의 리포트 생성 (권한 테스트용)
        self.other_report = Report.objects.create(
            user_id=self.other_user,
            title="다른 사용자의 리포트",
            description="다른 사용자 설명",
            type=Report.ReportType.QUESTION,
            status=Report.StatusType.OPEN,
        )

        # 처리중인 리포트 생성 (상태 테스트용)
        self.in_progress_report = Report.objects.create(
            user_id=self.user,
            title="처리중 리포트",
            description="처리중 설명",
            type=Report.ReportType.ERROR,
            status=Report.StatusType.IN_PROGRESS,
        )

        # URL 경로
        self.list_create_url = reverse("report-list-create")
        self.detail_url = lambda id: reverse("report-detail", kwargs={"id": id})

    def test_create_report_success(self):
        """리포트 생성 성공 테스트"""
        data = {
            "title": "새 리포트",
            "description": "새 리포트 설명",
            "type": Report.ReportType.FEATURE_REQUEST,
        }

        response = self.client.post(self.list_create_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Report.objects.count(), 4)  # 기존 3개 + 새로 생성된 1개
        self.assertEqual(response.data["title"], "새 리포트")
        self.assertEqual(response.data["type"], Report.ReportType.FEATURE_REQUEST)
        self.assertEqual(response.data["status"], Report.StatusType.OPEN)

    def test_create_report_missing_field(self):
        """필수 필드 누락 테스트"""
        # 필수 필드인 type 누락
        data = {
            "title": "새 리포트",
            "description": "새 리포트 설명",
        }

        response = self.client.post(self.list_create_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "MISSING_FIELD")

    def test_create_report_invalid_type(self):
        """유효하지 않은 타입 테스트"""
        data = {
            "title": "새 리포트",
            "description": "새 리포트 설명",
            "type": "INVALID_TYPE",
        }

        response = self.client.post(self.list_create_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "INVALID_TYPE")

    def test_create_report_title_too_long(self):
        """제목 길이 초과 테스트"""
        data = {
            "title": "a" * 101,  # 101 자 (제한은 100자)
            "description": "새 리포트 설명",
            "type": Report.ReportType.ERROR,
        }

        response = self.client.post(self.list_create_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "TITLE_TOO_LONG")

    def test_get_reports(self):
        """리포트 목록 조회 테스트"""
        response = self.client.get(self.list_create_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # 자신의 리포트 2개만 조회

        # 다른 사용자의 리포트는 포함되지 않음
        self.assertFalse(
            any(str(self.other_report.id) in str(r["id"]) for r in response.data)
        )

    def test_update_report_success(self):
        """리포트 수정 성공 테스트"""
        data = {
            "title": "수정된 제목",
            "description": "수정된 설명",
            "type": Report.ReportType.QUESTION,
        }

        response = self.client.put(self.detail_url(self.report.id), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "수정된 제목")
        self.assertEqual(response.data["type"], Report.ReportType.QUESTION)

        # DB에 실제로 수정되었는지 확인
        updated_report = Report.objects.get(id=self.report.id)
        self.assertEqual(updated_report.title, "수정된 제목")
        self.assertEqual(updated_report.type, Report.ReportType.QUESTION)

    def test_update_report_not_owner(self):
        """소유자가 아닌 리포트 수정 시도 테스트"""
        data = {
            "title": "수정된 제목",
            "description": "수정된 설명",
            "type": Report.ReportType.QUESTION,
        }

        response = self.client.put(
            self.detail_url(self.other_report.id), data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "FORBIDDEN")

    def test_update_report_locked(self):
        """처리중인 리포트 수정 시도 테스트"""
        data = {
            "title": "수정된 제목",
            "description": "수정된 설명",
            "type": Report.ReportType.QUESTION,
        }

        response = self.client.put(
            self.detail_url(self.in_progress_report.id), data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "REPORT_LOCKED")

    def test_delete_report_success(self):
        """리포트 삭제 성공 테스트"""
        response = self.client.delete(self.detail_url(self.report.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.report.id))

        # DB에서 실제로 삭제되었는지 확인
        with self.assertRaises(Report.DoesNotExist):
            Report.objects.get(id=self.report.id)

    def test_delete_report_not_owner(self):
        """소유자가 아닌 리포트 삭제 시도 테스트"""
        response = self.client.delete(self.detail_url(self.other_report.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "FORBIDDEN")

        # DB에서 삭제되지 않았는지 확인
        self.assertTrue(Report.objects.filter(id=self.other_report.id).exists())

    def test_unauthorized_access(self):
        """인증되지 않은 사용자 접근 테스트"""
        # 인증 해제
        self.client.force_authenticate(user=None)

        # 리포트 목록 조회 시도
        list_response = self.client.get(self.list_create_url)
        self.assertEqual(list_response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 리포트 생성 시도
        create_data = {
            "title": "새 리포트",
            "description": "새 리포트 설명",
            "type": Report.ReportType.ERROR,
        }
        create_response = self.client.post(
            self.list_create_url, create_data, format="json"
        )
        self.assertEqual(create_response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 리포트 수정 시도
        update_data = {
            "title": "수정된 제목",
            "description": "수정된 설명",
            "type": Report.ReportType.QUESTION,
        }
        update_response = self.client.put(
            self.detail_url(self.report.id), update_data, format="json"
        )
        self.assertEqual(update_response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 리포트 삭제 시도
        delete_response = self.client.delete(self.detail_url(self.report.id))
        self.assertEqual(delete_response.status_code, status.HTTP_401_UNAUTHORIZED)
