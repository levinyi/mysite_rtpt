# notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
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

@receiver(post_save, sender=User)
def user_registered_signal(sender, instance, created, **kwargs):
    if created:
        # 新用户创建成功时，假设我们有一个 “verify_link” 的生成逻辑
        # verify_link = f"https://rootpath.com.cn/verify/{instance.id}/token..."
        # 异步发送
        # async_send_registration_user_email.delay(instance.id, verify_link)
        async_send_registration_staff_notify.delay(instance.id)

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
    if created:
        # 文件上传成功时
        async_send_vector_uploaded_user_email.delay(instance.id)
        async_send_vector_uploaded_staff_notify.delay(instance.id)

@receiver(post_save, sender=Vector)
def vector_approved_signal(sender, instance, created, update_fields, **kwargs):
    # 需要区分一下，只要status 从其他状态变成了 ReadyToUse 就发送邮件
    if not created and instance.status == "ReadyToUse":
        async_send_vector_approved_user_email.delay(instance.id)
        async_send_vector_approved_staff_notify.delay(instance.id)