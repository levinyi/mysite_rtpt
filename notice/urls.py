from django.urls import path
from . import views

app_name = 'notice'

urlpatterns = [
    path('test/', views.test, name='test'),
    path('send_email/', views.send_email, name='send_email'),
]
