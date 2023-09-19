from django.urls import path
from . import views

app_name = 'user_center'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    # path('create_order/', views.create_order, name='create_order'),
    path('submit_order/<int:shopping_id>/', views.submit_order, name='submit_order'),
    path('shopping_cart/', views.shopping_cart, name='shopping_cart'),
    path('shopping_cart_remove/', views.shopping_cart_remove, name='shopping_cart_remove'),
    path('manage_order/', views.manage_order, name='manage_order'),
    path('manage_vector/', views.manage_vector, name='manage_vector'),
    path('vector_add/', views.vector_add, name='vector_add'),
    path('download_pdf/<int:order_id>/', views.download_pdf, name='download_pdf'),
]