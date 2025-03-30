import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def get_by_natural_key(self, email):
        return self.get(email=email)

    def create_user(self, email, nickname, password, phone_number=None, **kwargs):
        if not email:
            raise ValueError("올바른 이메일을 입력하세요.")

        user = self.model(
            email=self.normalize_email(email),
            nickname=nickname,
            phone_number=phone_number,
            **kwargs,
        )

        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    # 슈퍼 사용자 생성 , python manage.py createsuperuser
    def create_superuser(self, email, nickname, password, phone_number=None):
        user = self.create_user(email, nickname, password, phone_number)
        user.is_staff = True  # 관리자 페이지 접근 가능
        user.is_superuser = True  # 모든 권한 부여
        user.is_active = True  # 활성화 상태
        user.save(using=self._db)
        return user


# Create your models here.
class User(AbstractBaseUser):

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("SUSPENDED", "Suspended"),
        ("DELETED", "Deleted"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(verbose_name="email", unique=True)
    is_social = models.BooleanField(default=False)
    nickname = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, unique=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ACTIVE")
    profile_image = models.ImageField(
        null=True, blank=True, upload_to="profile_images/"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    login_attempts = models.IntegerField(default=0)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()
    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["nickname", "phone_number"]

    class Meta:
        verbose_name = "유저"
        verbose_name_plural = f"{verbose_name} 목록"

    def get_full_name(self):
        return self.nickname

    def get_short_name(self):
        return self.nickname

    def __str__(self):
        return self.nickname

    def has_perm(self, perm, obj=None):
        return self.is_superuser  # ✅ 슈퍼유저 권한 체크

    def has_module_perms(self, app_label):
        return self.is_superuser  # ✅ 슈퍼유저 권한 체크

    # @property
    # def is_superuser(self):
    #     return self.is_superuser

    def delete(self):
        self.is_active = False
        self.status = "DELETED"
        self.deleted_at = timezone.now()
        self.save()

    @classmethod
    def restore_user(cls, email):
        user = cls.objects.filter(email=email).first()
        if user:
            user.status = "ACTIVE"
            user.is_active = True
            user.deleted_at = None
            user.save()
        return user


