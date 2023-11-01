from django.urls import path
from . import views

app_name = 'user_center'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('submit_order/<int:shopping_id>/', views.submit_order, name='submit_order'),
    path('order_create/', views.order_create, name='order_create'),
    path('shopping_cart/', views.shopping_cart, name='shopping_cart'),
    path('shopping_cart_remove/', views.shopping_cart_remove, name='shopping_cart_remove'),


    path('manage_order/', views.manage_order, name='manage_order'),
    path('manage_vector/', views.manage_vector, name='manage_vector'),
    path('vector_add/', views.vector_add, name='vector_add'),
    path('vector_detail/<int:vector_id>/', views.vector_detail, name='vector_detail'),
    path('vector_edit/<int:vector_id>/', views.vector_edit, name='vector_edit'),
    path('vector_delete/<int:vector_id>/', views.vector_delete, name='vector_delete'),
    path('vector_validation/<int:vector_id>/', views.vector_validation, name='vector_validation'),
    path('validation_save/<int:vector_id>/', views.validation_save, name='validation_save'),
    # path('download_pdf/<int:order_id>/', views.download_pdf, name='download_pdf'),

]