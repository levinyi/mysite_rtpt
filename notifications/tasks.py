# notifications/tasks.py
from celery import shared_task
from django.contrib.auth import get_user_model
from user_center.models import Vector
from user_center.models import OrderInfo
from notifications.emails import (
    send_registration_user_email,
    send_registration_staff_notify,
    send_order_created_user_email,
    send_order_created_staff_notify,
    send_password_reset_user_email,
    send_vector_uploaded_user_email,
    send_vector_uploaded_staff_notify,
    send_vector_approved_user_email,
    send_vector_approved_staff_notify
)

@shared_task
def async_send_registration_user_email(user_id, verify_link):
    """
    异步发送注册邮件给用户
    注意这里要用 user_id，而不能直接传 user 对象(无法序列化)
    """
    User = get_user_model()
    user = User.objects.get(pk=user_id)
    send_registration_user_email(user, verify_link)

@shared_task
def async_send_registration_staff_notify(user_id):
    User = get_user_model()
    user = User.objects.get(pk=user_id)
    send_registration_staff_notify(user)


@shared_task
def async_send_order_created_user_email(order_id):
    print("order_id", order_id)
    order = OrderInfo.objects.get(pk=order_id)
    send_order_created_user_email(order)

@shared_task
def async_send_order_created_staff_notify(order_id):
    order = OrderInfo.objects.get(pk=order_id)
    send_order_created_staff_notify(order)

@shared_task
def async_send_password_reset_staff_notify(user_id):
    User = get_user_model()
    user = User.objects.get(pk=user_id)
    send_password_reset_staff_notify(user)

@shared_task
def async_send_password_reset_user_email(user_id, reset_link):
    User = get_user_model()
    user = User.objects.get(pk=user_id)
    send_password_reset_user_email(user, reset_link)

@shared_task
def async_send_vector_uploaded_user_email(vector_id):
    vector = Vector.objects.get(pk=vector_id)
    send_vector_uploaded_user_email(vector)

@shared_task
def async_send_vector_uploaded_staff_notify(vector_id):
    vector = Vector.objects.get(pk=vector_id)
    send_vector_uploaded_staff_notify(vector)

@shared_task
def async_send_vector_approved_user_email(vector_id):
    vector = Vector.objects.get(pk=vector_id)
    send_vector_approved_user_email(vector)

@shared_task
def async_send_vector_approved_staff_notify(vector_id):
    vector = Vector.objects.get(pk=vector_id)
    send_vector_approved_staff_notify(vector)