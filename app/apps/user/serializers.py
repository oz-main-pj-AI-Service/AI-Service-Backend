import redis
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers, status
from rest_framework.exceptions import APIException

# Create your views here.

User = get_user_model()
redis_client = redis.StrictRedis(
    host="localhost", port=6379, db=0, decode_responses=True
)


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


class UserRegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "password1", "password2", "nickname", "phone_number")

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError(
                {"password": "비밀번호가 일치하지 않습니다."}
            )
        return data

    def validate_email(self, value):
        """이메일 중복 검사"""
        if User.objects.filter(email=value).exists():
            raise ConflictException(
                detail="이미 사용중인 이메일 입니다.", code="email_conflict"
            )
        return value

    def validate_password1(self, value):
        validate_password(value)
        return value

    def validate_phone_number(self, value):
        """핸드폰 번호 숫자만 가능"""
        if not value.isdigit():
            raise serializers.ValidationError("핸드폰 번호는 숫자만 입력해야 합니다.")
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
                {"new_password": "비밀번호가 일치하지 않습니다."}
            )
        return data

    def update(self, instance, validated_data):
        """비밀번호 변경 로직"""
        user = instance

        # 현재 비밀번호 확인
        if not user.check_password(validated_data["old_password"]):
            raise serializers.ValidationError(
                {"old_password": "현재 비밀번호가 올바르지 않습니다."}
            )

        # 새 비밀번호 설정
        user.set_password(validated_data["new_password1"])
        user.save()

        # 세션 유지 (로그인 상태 유지)
        update_session_auth_hash(self.context["request"], user)

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
