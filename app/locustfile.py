# locustfile.py
from locust import HttpUser, between, task


class UserBehavior(HttpUser):
    host = "http://127.0.0.1:8000"
    wait_time = between(1, 3)  # 요청 간 간격 (초)

    def on_start(self):
        response = self.client.post(
            "/api/user/login/",
            json={"email": "test@example.com", "password": "!!test1234"},
        )

        data = response.json()
        self.access_token = data.get("access_token")
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

    @task
    def get_profile(self):
        self.client.get("/api/user/profile/", headers=self.headers)

    @task
    def update_profile(self):
        self.client.patch(
            "/api/user/profile/",
            headers=self.headers,
            json={"nickname": "updated_nick"},
        )

    @task
    def logout(self):
        self.client.post("/api/user/logout/", headers=self.headers)
