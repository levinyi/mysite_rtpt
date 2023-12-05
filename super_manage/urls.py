from django.urls import path
from . import views

app_name = 'super_manage'

urlpatterns = [
    path('order_manage/', views.order_manage, name='order_manage'),
    path('vector_manage/', views.vector_manage, name='vector_manage'),
    path('change_status/', views.change_status, name='change_status'),
    path('change_url/', views.change_url, name='change_url'),
    path('change_status/get_rows', views.get_rows, name='get_rows'),
]