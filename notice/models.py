# notice/models.py
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from account.models import UserProfile

import hashlib

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

    token = models.CharField(max_length=255, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    verify_type = models.CharField(max_length=10, choices=VERIFY_TYPE_CHOICES)
    create_time = models.DateTimeField(default=timezone.now)
    expired_time = models.DateTimeField()
    code = models.IntegerField(blank=True, null=True)
    used = models.BooleanField(default=False)

    @classmethod
    def verify_code(cls, phone, code):
        print(phone,code)
        if not code or not phone:
            return False, None
        try:
            notice = Notice.objects.get(code=code,
                                        user__userprofile__phone=phone,
                                        user__userprofile__is_verify=False)
        except Notice.DoesNotExist:
            return False, None
        print('ok?',notice)
        if not notice or notice.expired_time < timezone.now() or notice.used:
            return False, notice
        notice.used = True
        notice.save()
        return True, notice

    @classmethod
    def verify_link(cls, uidb64, token):
        # 根据解密后的 user_id 和 verify_code 获取对应的 Notice 记录
        user = cls.get_user_from_uidb64(uidb64)
        notice = Notice.objects.get(user=user.id, token=token)
        if not notice or notice.expired_time < timezone.now() or notice.used:
            return False, notice
        notice.used = True
        notice.save()
        return True, notice

    @classmethod
    def get_user_from_uidb64(cls, uidb64):
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

    @classmethod
    def generate_verification_code(cls, token):
        # 使用SHA-256哈希算法
        hashed_token = hashlib.sha256(token.encode()).hexdigest()
        # 将哈希值映射到6位数字
        numeric_code = int(hashed_token, 16) % (10 ** 6)
        return numeric_code

    @classmethod
    def create(cls, user, purpose, verify_type):
        # 创建对象时设置初始值
        token = default_token_generator.make_token(user)
        if verify_type.lower() == 'phone':
            code = cls.generate_verification_code(token)
        else:
            code = None
        create_time = timezone.now()
        expired_time = create_time + timezone.timedelta(days=1)
        return cls(user=user, purpose=purpose, verify_type=verify_type, token=token, create_time=create_time,
                   expired_time=expired_time, code=code)

    def get_uidb64(self):
        return urlsafe_base64_encode(str(self.user.id).encode(encoding='utf-8'))

    def get_verification_url(self):
        path = reverse('account:verify', args=[self.get_uidb64(), self.token])
        return path  # 替换为你的域名

    def clean(self):
        # 自定义验证逻辑，确保 status 的值在 choices 中
        if self.purpose not in dict(self.PURPOSE_CHOICES).keys():
            raise ValidationError(f"Invalid value for purpose: {self.purpose}")
        if self.verify_type not in dict(self.VERIFY_TYPE_CHOICES).keys():
            raise ValidationError(f"Invalid value for verify type: {self.verify_type}")

    def __str__(self):
        return f"{self.user.username} - {self.purpose} - {self.verify_type} - {self.verify_code}"
