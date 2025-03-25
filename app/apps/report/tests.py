import json

from apps.report.models import Report
from django.contrib.auth import get_user_model
from django.test.testcases import TestCase
from django.urls.base import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class ReportModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com",
            nickname="test",
            password="test1234",
            phone_number="1234",
        )

    def test_create_report(self):
        report = Report.objects.create(
            user_id=self.user,
            title="Test Report",
            description="Test description",
            status="IN_PROGRESS",
            type="QUESTION",
        )

        self.assertEqual(Report.objects.all().count(), 1)
        self.assertEqual(report.user_id, self.user)
        self.assertEqual(report.title, "Test Report")


class ReportAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com",
            nickname="test",
            password="test1234",
            phone_number="1234",
        )
        self.user2 = User.objects.create_user(
            email="test2@test.com",
            nickname="test",
            password="test1234",
            phone_number="12345",
        )
        self.super_user = User.objects.create_superuser(
            email="admin_test@test.com",
            nickname="admin_test",
            password="test1234",
        )

        self.data = {
            "title": "Test Report",
            "description": "Test description",
            "status": "IN_PROGRESS",
            "type": "QUESTION",
        }
        self.data2 = {
            "title": "Test Report2",
            "description": "Test description2",
            "status": "IN_PROGRESS",
            "type": "QUESTION",
        }

        self.report_list_create_url = reverse("report:list-create")

    def test_report_create_list(self):
        response = self.client.post(self.report_list_create_url, self.data)
        self.assertEqual(response.status_code, 401)

        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(token.access_token))

        response = self.client.post(self.report_list_create_url, data=self.data)
        self.assertEqual(Report.objects.all().count(), 1)
        self.assertEqual(response.data["title"], "Test Report")
        self.assertEqual(response.data["description"], "Test description")
        self.assertEqual(response.data["status"], "IN_PROGRESS")
        self.assertEqual(response.data["type"], "QUESTION")

        self.client.post(self.report_list_create_url, data=self.data2)
        self.assertEqual(Report.objects.all().count(), 2)

        response = self.client.get(self.report_list_create_url)
        titles = [item["title"] for item in response.data["results"]]
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Report", titles)
        self.assertIn("Test Report2", titles)

    def test_report_detail_update_destroy(self):
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(token.access_token))
        response = self.client.post(self.report_list_create_url, data=self.data)
        # Detail TEST
        # report id를 찾기위해 reveres를 통해 pk를 넣어야 하는데 만들어진 상황에서 가져올수 있어서 self.url 사용 X
        url = reverse(
            "report:detail-update-destroy", kwargs={"pk": response.data.get("id")}
        )
        response = self.client.get(url)
        self.assertEqual(response.data["title"], "Test Report")
        self.assertEqual(response.data["description"], "Test description")
        self.assertEqual(response.data["status"], "IN_PROGRESS")
        self.assertEqual(response.data["type"], "QUESTION")

        # PATCH TEST
        response = self.client.patch(url, data=self.data2)
        self.assertEqual(response.data["title"], "Test Report2")
        self.assertEqual(response.data["description"], "Test description2")

        # 403 에러 테스트 : 작성자
        token = RefreshToken.for_user(self.user2)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(token.access_token))
        response = self.client.patch(url, data=self.data)
        self.assertEqual(response.status_code, 403)

        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(token.access_token))
        # DELETE TEST
        response = self.client.delete(url)
        self.assertEqual(Report.objects.all().count(), 0)
        self.assertEqual(response.status_code, 204)

    def test_admin_list_update(self):
        token1 = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(token1.access_token))
        response = self.client.post(self.report_list_create_url, self.data)
        self.client.post(self.report_list_create_url, self.data)

        id = str(response.data.get("id"))

        token2 = RefreshToken.for_user(self.super_user)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(token2.access_token))
        self.client.post(self.report_list_create_url, self.data)

        # 관리자 수정 여부
        url = reverse("report:admin-update", kwargs={"pk": id})
        response = self.client.patch(url, data={"admin_comment": "Test Comment"})
        self.assertEqual(response.status_code, 200)

        # 관리자여서 3
        response = self.client.get(self.report_list_create_url)
        self.assertEqual(len(response.data["results"]), 3)
        token1 = RefreshToken.for_user(self.user)

        # 일반유저 2
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(token1.access_token))
        response = self.client.get(self.report_list_create_url)
        self.assertEqual(len(response.data["results"]), 2)

        # 일반 유저 수정 테스트
        url = reverse("report:admin-update", kwargs={"pk": id})
        response = self.client.patch(url, data={"admin_comment": "Test Comment"})
        self.assertEqual(response.status_code, 403)
