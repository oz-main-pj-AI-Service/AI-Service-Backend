from apps.report.models import Report
from django.contrib.auth import get_user_model
from django.test.testcases import TestCase
from django.urls.base import reverse
from rest_framework.test import APITestCase

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
        self.super_user = User.objects.create_superuser(
            email="admin_test@test.com",
            nickname="admin_test",
            password="test1234",
        )

        self.report_list_create_url = reverse("report:report-list-create")
        self.report_detail_update_url = reverse("report:report-list-create")
        self.report_list_create_url = reverse("report:report-list-create")
