from django.test import TestCase

# Create your tests here.

from django.test import TestCase
from django.core import mail

from account.models import UserProfile
from .views import send_email_with_link
from .models import Notice
# from unittest.mock import patch
from django.contrib.auth.models import User
from .views import send_sms_with_code



class SendEmailWithLinkTest(TestCase):
    def setUp(self):
        # 创建一个测试用户
        self.user = User.objects.create_user(username='testuser', email='xxxx', password='12345')

    def test_send_email_with_link(self):
        # 调用 send_email_with_link 函数
        result = send_email_with_link(self.user, 'reset', 'Test email')

        # 检查返回值
        self.assertTrue(result)

        # 检查是否创建了 Notice 记录
        self.assertTrue(Notice.objects.filter(user=self.user, verify_type='Email', purpose='reset').exists())

        # 检查是否发送了邮件
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Test email')
        self.assertEqual(mail.outbox[0].to, ['xxxxx'])
        print(mail.outbox[0].from_email)
        # 检查邮件内容
        self.assertIn('Click the link to verify your reset', mail.outbox[0].body)


# FILEPATH: /e:/7.工作/rootpath/mysite_rtpt/notice/tests.py

class SendSmsWithCodeTest(TestCase):
    def setUp(self):
        # 创建一个测试用户
        self.user = User.objects.create_user(username='hello',password='12345')
        self.up = UserProfile.objects.create(phone='xxxxxx',user=self.user)
        self.user.save()
        self.up.save()

    def test_send_sms_with_code(self):
        # 调用 send_sms_with_code 函数
        result = send_sms_with_code(self.user, 'reset')

        # 检查返回值
        self.assertTrue(result)

        # 检查是否创建了 Notice 记录
        self.assertTrue(Notice.objects.filter(user=self.up.user, verify_type='phone', purpose='reset').exists())

