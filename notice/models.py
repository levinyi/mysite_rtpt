# notice/models.py
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from account.models import UserProfile


def get_user(uidb64):
    try:
        # urlsafe_base64_decode() decodes to bytestring
        uid = urlsafe_base64_decode(uidb64).decode()
        print(uid)
        user = User.objects.get(id=uid)
    except (
        TypeError,
        ValueError,
        OverflowError,
        User.DoesNotExist,
        ValidationError,
    ):
        user = None
    return user


class Notice(models.Model):
    VERIFY_TYPE_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
    ]

    PURPOSE_CHOICES = [
        ('reset', 'Reset'),
        ('verify', 'Verify'),
        ('login', 'Login'),
        ('signup', 'Signup'),
    ]

    token = models.CharField(max_length=255,primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    verify_type = models.CharField(max_length=10, choices=VERIFY_TYPE_CHOICES)
    create_time = models.DateTimeField(default=timezone.now)
    expired_time = models.DateTimeField()
    used = models.BooleanField(default=False)

    @classmethod
    def create(cls, user, purpose, verify_type):
        # 创建对象时设置初始值
        token = default_token_generator.make_token(user)
        create_time = timezone.now()
        expired_time = create_time + timezone.timedelta(days=1)
        return cls(user=user, purpose=purpose, verify_type=verify_type, token=token, create_time=create_time, expired_time=expired_time)


    def get_verification_url(self):
        uidb64 = urlsafe_base64_encode(str(self.user.id).encode(encoding='utf-8'))
        path = reverse('account:verify', args=[uidb64, self.token])
        return path  # 替换为你的域名

    def clean(self):
        # 自定义验证逻辑，确保 status 的值在 choices 中
        if self.purpose not in dict(self.PURPOSE_CHOICES).keys():
            raise ValidationError(f"Invalid value for purpose: {self.purpose}")
        if self.verify_type not in dict(self.VERIFY_TYPE_CHOICES).keys():
            raise ValidationError(f"Invalid value for verify type: {self.verify_type}")

    def __str__(self):
        return f"{self.user.username} - {self.purpose} - {self.verify_type} - {self.verify_code}"
