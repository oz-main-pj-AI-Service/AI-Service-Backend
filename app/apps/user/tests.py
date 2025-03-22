from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APITestCase

User = get_user_model()


# Create your tests here.
class UserModelTest(TestCase):
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

    def test_create_user(self):
        self.assertEqual(self.super_user.is_superuser, True)
        self.assertEqual(self.user.is_superuser, False)
        self.assertEqual(User.objects.all().count(), 2)


from apps.user.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class TestUserViews(APITestCase):
    def setUp(self):
        self.register_url = reverse("user:register")
        self.login_url = reverse("user:login")
        self.logout_url = reverse("user:logout")
        self.profile_url = reverse("user:profile")
        self.change_password_url = reverse("user:change-pw")

    def test_user_register(self):
        data = {
            "email": "test@test.com",
            "nickname": "test",
            "password1": "!!test1234",
            "password2": "!!test1234",
            "phone_number": "1234",
        }

        response = self.client.post(self.register_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_view(self):
        # 먼저 회원가입이 필요함
        data = {
            "email": "test@test.com",
            "nickname": "test",
            "password1": "!!test1234",
            "password2": "!!test1234",
            "phone_number": "1234",
        }
        self.client.post(self.register_url, data, format="json")

        # 이메일 인증이 필요함
        user = User.objects.get(email="test@test.com")
        user.email_verified = True
        user.save()
        # 테스트 환경에서는 이메일 인증을 생략하거나, 인증된 사용자를 생성해야 함

        login_data = {
            "email": "test@test.com",
            "password": "!!test1234",
        }
        response = self.client.post(self.login_url, login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        access_token = response.data["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        change_data = {
            "old_password": "!!test1234",
            "new_password1": "!!test12345",
            "new_password2": "!!test12345",
        }
        response = self.client.post(
            self.change_password_url, change_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestFindEmailView(APITestCase):
    def setUp(self):
        self.find_email_url = reverse("user:find-email")

    def test_find_email(self):
        # 먼저 사용자를 생성해야 함
        self.user = User.objects.create_user(
            email="existing@example.com",
            nickname="test",
            password="test1234",
            phone_number="01012345678",
        )

        data = {
            "phone_number": "01012345678",
        }
        response = self.client.post(self.find_email_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
