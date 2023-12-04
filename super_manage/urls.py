from django.urls import path
from . import views

app_name = 'super_manage'

urlpatterns = [
    path('order_manage/', views.order_manage, name='order_manage'),
    path('vector_manage/', views.vector_manage, name='vector_manage'),
]