# notice/views.py
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from .models import Notice, get_user
from django.conf import settings


def send_email_with_link(user, purpose, subject, message=''):
    """
    user:user model
    purpose:[
        ('reset', 'Reset'),
        ('verify', 'Verify'),
        ('login', 'Login'),
        ('signup', 'Signup'),
    ]
    subject: Subject of the email
    """
    try:
        # 创建 Notice 记录, 必须使用Notice.create才能正确create模型
        notice = Notice.create(user=user, verify_type='Email', purpose=purpose)
        notice.save()
    except ValidationError as e:
        return False

    # 发送邮件
    send_mail(
        subject,
        message + f" Click the link to verify your {purpose}: {settings.BASE_URL}{notice.get_verification_url()}",
        'zsl503503@163.com',  # 发件人邮箱
        [user.email]  # 收件人邮箱
    )
    return True
