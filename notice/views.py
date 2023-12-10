# notice/views.py
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.http import Http404

from account.models import UserProfile
from .models import Notice
from django.conf import settings

import os
import sys

from typing import List

from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


def send_email_with_link(user, purpose, subject, message=""):
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
        notice = Notice.create(user=user, verify_type="Email", purpose=purpose)
        notice.save()
    except ValidationError as e:
        return False

    # 发送邮件
    send_mail(
        subject,
        message
        + f" Click the link to verify your {purpose}: {settings.BASE_URL}{notice.get_verification_url()}",
        "zsl503503@163.com",  # 发件人邮箱
        [user.email],  # 收件人邮箱
    )
    return True


def create_sms_client(
        access_key_id: str,
        access_key_secret: str,
) -> Dysmsapi20170525Client:
    """
    使用AK&SK初始化账号Client
    @param access_key_id:
    @param access_key_secret:
    @return: Client
    @throws Exception
    """
    config = open_api_models.Config(
        # 必填，您的 AccessKey ID,
        access_key_id=access_key_id,
        # 必填，您的 AccessKey Secret,
        access_key_secret=access_key_secret,
    )
    # Endpoint 请参考 https://api.aliyun.com/product/Dysmsapi
    config.endpoint = f"dysmsapi.aliyuncs.com"
    return Dysmsapi20170525Client(config)


def send_sms_with_code(user:User, purpose) -> bool:
    # 请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID 和 ALIBABA_CLOUD_ACCESS_KEY_SECRET。
    # 工程代码泄露可能会导致 AccessKey 泄露，并威胁账号下所有资源的安全性。以下代码示例使用环境变量获取 AccessKey 的方式进行调用，
    # 仅供参考，建议使用更安全的 STS 方式，更多鉴权访问方式请参见：https://help.aliyun.com/document_detail/378659.html
    if not user.userprofile.phone:
        return False
    if "ALIBABA_CLOUD_ACCESS_KEY_ID" not in os.environ or "ALIBABA_CLOUD_ACCESS_KEY_SECRET" not in os.environ:
        print("请配置环境变量ALIBABA_CLOUD_ACCESS_KEY_ID和ALIBABA_CLOUD_ACCESS_KEY_SECRET")
        raise Http404(
            "No ALIBABA_CLOUD_ACCESS_KEY_ID or ALIBABA_CLOUD_ACCESS_KEY_SECRET"
        )

    try:
        # 创建 Notice 记录, 必须使用Notice.create才能正确create模型

        notice = Notice.create(user=user, verify_type="phone", purpose=purpose)
        notice.save()
    except ValidationError as e:
        return False

    client = create_sms_client(
        os.environ["ALIBABA_CLOUD_ACCESS_KEY_ID"],
        os.environ["ALIBABA_CLOUD_ACCESS_KEY_SECRET"],
    )
    if purpose == "reset":
        # 看情况选择短信模板
        template_code = "SMS_154950909"
    else:
        template_code = "SMS_154950909"

    send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
        sign_name="阿里云短信测试",
        template_code=template_code,
        phone_numbers=user.userprofile.phone,
        template_param='{"code":"' + str(notice.code) + '"}',
    )
    try:
        # 复制代码运行请自行打印 API 的返回值
        client.send_sms(send_sms_request)
        return True
    except Exception as error:
        # 错误 message
        print(error.message)
        # 诊断地址
        print(error.data.get("Recommend"))
        UtilClient.assert_as_string(error.message)
        return False

