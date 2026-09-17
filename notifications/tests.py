from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase

from product.models import Vector


class VectorUploadedNotifyTests(TestCase):
    """上传通知要等事务提交后再投递，否则 worker 抢在提交前查库会 Vector.DoesNotExist。"""

    def test_staff_notify_is_deferred_until_commit(self):
        customer = User.objects.create_user('notify_customer', password='x')
        with mock.patch('notifications.signals.async_send_vector_uploaded_staff_notify') as task:
            with self.captureOnCommitCallbacks(execute=False) as callbacks:
                vector = Vector.objects.create(user=customer, vector_name='pCVa999 test', status='Submitted')
                task.delay.assert_not_called()
            for callback in callbacks:
                callback()
        task.delay.assert_called_once_with(vector.id)
