import os
from celery import Celery

# 设置Django的默认设置模块。
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

app = Celery('mysite')

# 使用字符串这里意味着工作者(worker)不用序列化配置对象到子进程中去。
# - namespace='CELERY' 表示所有与celery相关的配置键应该有一个`CELERY_`的前缀。
app.config_from_object('django.conf:settings', namespace='CELERY')

# 加载 task 模块，所有注册的Django app下的task.py。
app.autodiscover_tasks()