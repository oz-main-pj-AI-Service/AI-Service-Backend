from apps.log.models import ActivityLog
from apps.report.models import Report
from django.contrib.auth import get_user_model
from django.test.testcases import TestCase
from django.urls.base import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class ActivityLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com",
            nickname="test",
            password="test1234",
            phone_number="1234",
        )

    def test_create_activity_log(self):

        log = ActivityLog.objects.create(
            user_id=self.user,
            action="LOGIN",
            ip_address="127.0.0.1",
            details={"test": "test"},
        )
        self.assertEqual(ActivityLog.objects.all().count(), 1)
        self.assertEqual(log.action, "LOGIN")
        self.assertEqual(log.ip_address, "127.0.0.1")
        self.assertEqual(log.details["test"], "test")


class ActivityLogAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com",
            nickname="test",
            password="test1234",
            phone_number="1234",
            email_verified=True,
        )
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(token.access_token))

    def test_login_log(self):
        self.client.post(
            reverse("user:login"),
            data={"email": "test@test.com", "password": "test1234"},
        )

        log = ActivityLog.objects.all()
        self.assertEqual(log.count(), 1)
        self.assertEqual(log.filter(user_id=self.user).first().action, "LOGIN")
        self.assertEqual(log.filter(user_id=self.user).first().ip_address, "127.0.0.1")

    def test_logout_log(self):
        self.client.post(reverse("user:logout"))

        log = ActivityLog.objects.all()
        self.assertEqual(log.count(), 1)
        self.assertEqual(log.filter(user_id=self.user).first().action, "LOGOUT")
        self.assertEqual(log.filter(user_id=self.user).first().ip_address, "127.0.0.1")

    def test_update_log(self):
        self.client.patch(reverse("user:profile"), data={"nickname": "test_log"})

        log = ActivityLog.objects.all()
        self.assertEqual(log.count(), 1)
        self.assertEqual(log.filter(user_id=self.user).first().action, "UPDATE_PROFILE")
        self.assertEqual(log.filter(user_id=self.user).first().ip_address, "127.0.0.1")
        self.assertEqual(
            log.filter(user_id=self.user).first().details["nickname"], "test_log"
        )

    def test_delete_log(self):
        self.client.delete(reverse("user:profile"))

        log = ActivityLog.objects.all()
        self.assertEqual(log.count(), 1)

    def test_report_view_log(self):
        self.client.get(reverse("report:list-create"))

        log = ActivityLog.objects.all()
        self.assertEqual(log.count(), 1)
        self.assertEqual(log.filter(user_id=self.user).first().action, "VIEW_REPORT")

    def test_report_create_update_log(self):
        self.client.post(
            reverse("report:list-create"),
            data={
                "title": "Test Report",
                "description": "Test description",
                "status": "IN_PROGRESS",
                "type": "QUESTION",
            },
        )

        # Create Log
        log = ActivityLog.objects.all()
        self.assertEqual(log.count(), 1)
        self.assertEqual(log.filter(user_id=self.user).first().action, "CREATE_REPORT")
        self.assertEqual(
            log.filter(user_id=self.user).first().details["title"], "Test Report"
        )
        id = Report.objects.filter(user_id=self.user).first().id
        # Update Log
        self.client.patch(
            reverse("report:detail-update-destroy", kwargs={"pk": id}),
            data={"title": "Update_Report"},
        )

        self.assertEqual(log.count(), 2)
        self.assertEqual(log.filter(user_id=self.user).first().action, "UPDATE_REPORT")
        self.assertEqual(
            log.filter(user_id=self.user).first().details["title"], "Update_Report"
        )

        # Profile Detail Get log
        self.client.get(reverse("report:detail-update-destroy", kwargs={"pk": id}))

        self.assertEqual(log.count(), 3)
        self.assertEqual(log.filter(user_id=self.user).first().action, "VIEW_REPORT")

        # Profile Delete Log
        self.client.delete(reverse("report:detail-update-destroy", kwargs={"pk": id}))

        self.assertEqual(log.count(), 4)
        self.assertEqual(log.filter(user_id=self.user).first().action, "DELETE_REPORT")

        self.client.post(
            reverse("report:list-create"),
            data={
                "title": "Test Report",
                "description": "Test description",
                "status": "IN_PROGRESS",
                "type": "QUESTION",
            },
        )
        id = Report.objects.filter(user_id=self.user).first().id

        # 관리자 업데이트
        super_user = User.objects.create_superuser(
            email="admin_test@test.com",
            nickname="admin_test",
            password="test1234",
        )
        self.assertEqual(log.count(), 5)

        token = RefreshToken.for_user(super_user)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(token.access_token))
        # PATCH 요청
        response = self.client.patch(
            reverse("report:admin-update", kwargs={"pk": id}),
            data={"admin_comment": "test_log"},
        )
        self.assertEqual(log.count(), 6)
        self.assertEqual(log.filter(user_id=super_user).first().action, "UPDATE_REPORT")
        self.assertEqual(
            log.filter(user_id=super_user).first().details["admin_comment"], "test_log"
        )

    def test_list_view_log(self):
        url = reverse("log:list-create")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.post(
            reverse("report:list-create"),
            data={
                "title": "Test Report",
                "description": "Test description",
                "status": "IN_PROGRESS",
                "type": "QUESTION",
            },
        )
        id = ActivityLog.objects.filter(user_id=self.user).first().id

        url = reverse("log:retrieve", kwargs={"pk": id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
