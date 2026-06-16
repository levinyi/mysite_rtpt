# notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from allauth.account.signals import email_confirmed, user_signed_up
from notifications.tasks import (
    async_send_registration_user_email,
    async_send_registration_staff_notify,
    async_send_password_reset_user_email,
    async_send_order_created_user_email,
    async_send_order_created_staff_notify,
    async_send_vector_approved_user_email,
    async_send_vector_approved_staff_notify,
    async_send_vector_uploaded_user_email,
    async_send_vector_uploaded_staff_notify,
)
from product.models import Vector
from user_center.models import OrderInfo
User = get_user_model()

# ── 注册通知：改为「邮箱验证通过后」才通知管理员（防机器人刷收件箱）──────────────
# 旧逻辑是 post_save(User, created) 一建号就通知，导致机器人用任意域名（含 gmail/
# yahoo）批量注册时管理员被刷屏。改成下面两个信号后：
#   - 普通邮箱注册：用户点了验证链接（email_confirmed）才通知 → 机器人不验证 = 不通知；
#   - 社交登录（飞书等，无邮箱验证环节）：注册即视为可信内部用户，立即通知。
@receiver(email_confirmed)
def notify_staff_on_email_confirmed(request, email_address, **kwargs):
    async_send_registration_staff_notify.delay(email_address.user_id)


@receiver(user_signed_up)
def notify_staff_on_social_signup(request, user, **kwargs):
    # 仅社交登录（kwargs 带 sociallogin）即时通知；普通邮箱注册等 email_confirmed。
    if kwargs.get('sociallogin') is not None:
        async_send_registration_staff_notify.delay(user.id)

# @receiver(post_save, sender=User)
# def user_password_reset_signal(sender, instance, created, **kwargs):
#     if not created:
#         # 用户重置密码时，假设我们有一个 “reset_link” 的生成逻辑
#         reset_link = f"https://rootpath.com.cn/reset/{instance.id}/token..."
#         # 异步发送
#         async_send_password_reset_user_email.delay(instance.id, reset_link)

@receiver(post_save, sender=OrderInfo)
def order_created_signal(sender, instance, created, **kwargs):
    if created:
        # 新订单创建成功时
        print("order_created_signal", instance.id)
        async_send_order_created_user_email.delay(instance.id)
        async_send_order_created_staff_notify.delay(instance.id)

@receiver(post_save, sender=Vector)
def vector_uploaded_signal(sender, instance, created, **kwargs):
    # 只在“用户(非 RootPath)提交了一个尚未 ReadyToUse 的载体”时通知管理员去 design。
    # 排除：RootPath 目录导入(user=None)、管理员直接建成的 ReadyToUse 载体。
    if created and instance.user_id and (instance.status or '').lower() != 'readytouse':
        async_send_vector_uploaded_staff_notify.delay(instance.id)

@receiver(post_save, sender=Vector)
def vector_approved_signal(sender, instance, created, update_fields, **kwargs):
    # 需要区分一下，只要status 从其他状态变成了 ReadyToUse 就发送邮件
    if not created and instance.status == "ReadyToUse":
        async_send_vector_approved_user_email.delay(instance.id)
        async_send_vector_approved_staff_notify.delay(instance.id)