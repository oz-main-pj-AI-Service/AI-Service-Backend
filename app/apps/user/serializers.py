import redis
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, status
from rest_framework.exceptions import APIException

# Create your views here.

User = get_user_model()
redis_client = redis.StrictRedis(
    host="localhost", port=6379, db=0, decode_responses=True
)


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="이메일 입력")
    password = serializers.CharField(help_text="비밀번호 입력")


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField(help_text="인증을 위한 토큰")


class ConflictException(APIException):
    status_code = status.HTTP_409_CONFLICT
    # default_code = "conflict"


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(help_text="리프레시 토큰", required=True)


class AccessTokenSerializer(serializers.Serializer):
    access_token = serializers.CharField(help_text="새로 발급된 엑세스 토큰")
    token_type = serializers.CharField(help_text="토큰 타입 : Bearer")
    expires_in = serializers.CharField(help_text="토큰 만료 시간")


class SocialUserCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def create(self, validated_data):
        email = validated_data["email"]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "is_social": True,
                "nickname": f'User_{email.split("@")[0]}',
                "status": "ACTIVE",
                "is_active": True,
                "phone_number": None,  # 필수 필드이므로 빈 문자열로 설정
                "profile_image": None,  # 선택 사항
                "login_attempts": 0,  # 기본값
                "email_verified": True,  # 기본값
            },
        )
        redis_client.set(f"user:{email}", "true", ex=3600 * 24)

        return user


class CustomCharField(serializers.CharField):
    def run_validation(self, data=serializers.empty):
        try:
            return super().run_validation(data)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError(
                {
                    "code": "required_field_missing",
                    "error": self.error_messages["required"],
                }
            )


class UserRegisterSerializer(serializers.ModelSerializer):
    email = CustomCharField()
    password1 = CustomCharField(write_only=True)
    password2 = CustomCharField(write_only=True)
    nickname = CustomCharField()
    phone_number = CustomCharField()

    class Meta:
        model = User
        fields = ("email", "password1", "password2", "nickname", "phone_number")

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError(
                detail="비밀번호가 불일치", code="password_mismatch"
            )

        return data

    def validate_email(self, value):
        """이메일 중복 검사"""
        user = User.objects.filter(email=value).first()
        if user:
            if user.is_social:
                raise ConflictException(
                    detail="소셜 가입자 입니다 소셜로 로그인 하세요", code="social_user"
                )
            raise ConflictException(
                detail="이미 사용중인 이메일 입니다.", code="email_conflict"
            )
        return value

    def validate_password1(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                detail="비밀번호는 너무 짧습니다.", code="password_invalid"
            )
        return value

    def validate_phone_number(self, value):
        """핸드폰 번호 숫자만 가능"""
        if not value.isdigit():
            raise serializers.ValidationError(
                "핸드폰 번호는 숫자만 입력해야 합니다.", code="invalid_number"
            )
        if User.objects.filter(phone_number=value).exists():
            raise ConflictException(
                "이미 사용 중인 핸드폰 번호입니다.", code="phone_number_conflict"
            )
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            nickname=validated_data["nickname"],
            password=validated_data["password1"],
            phone_number=validated_data["phone_number"],
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "nickname", "phone_number", "profile_image")
        read_only_fields = ("email",)

        def update(self, instance, validated_data):
            """유저 프로필 업데이트 로직"""
            instance.nickname = validated_data.get("nickname", instance.nickname)
            instance.phone_number = validated_data.get(
                "phone_number", instance.phone_number
            )
            instance.profile_image = validated_data.get(
                "profile_image", instance.profile_image
            )

            instance.save()


class UserChangePasswordSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password1 = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    new_password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("old_password", "new_password1", "new_password2")

    def validate(self, data):
        """새 비밀번호 일치 여부 확인"""
        if data["new_password1"] != data["new_password2"]:
            raise serializers.ValidationError(
                detail="비밀번호 불일치", code="password_mismatch"
            )
        return data

    def update(self, instance, validated_data):
        """비밀번호 변경 로직"""
        user = instance

        # 현재 비밀번호 확인
        if not user.check_password(validated_data["old_password"]):
            raise serializers.ValidationError(
                detail="현재 비밀번호 가 일치하지 않음", code="old_password_mismatch"
            )

        # 새 비밀번호 설정
        user.set_password(validated_data["new_password1"])
        user.save()

        return user


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nickname",
            "phone_number",
            "status",
            "profile_image",
            "created_at",
            "updated_at",
            "login_attempts",
            "is_active",
            "email_verified",
            "deleted_at",
        ]
