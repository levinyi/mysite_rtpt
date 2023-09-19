from django.urls import path
from . import views

app_name = 'product'
urlpatterns = [
    path('product_list/', views.product_list, name='product_list'),
    path('create_order/', views.create_order, name='create_order'),
    path('order_selection/<int:order_id>/', views.order_selection, name='order_selection'),
    path('order_quotation/<int:order_id>/', views.order_quotation, name='order_quotation'),
]