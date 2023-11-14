from django.urls import path
from . import views

app_name = 'user_center'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('order_create/', views.order_create, name='order_create'),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('gene_detail/', views.gene_detail, name='gene_detail'),
    path('gene_edit/<int:gene_id>/', views.gene_edit, name='gene_edit'),
    path('gene_delete/<int:gene_id>/', views.gene_delete, name='gene_delete'),
    path('gene_validation/', views.gene_validation, name='gene_validation'),
    path('view_cart/', views.view_cart, name='view_cart'),
    path('checkout/', views.checkout, name='checkout'),
    # path('submit_order/<int:shopping_id>/', views.submit_order, name='submit_order'),
    # path('shopping_cart/', views.shopping_cart, name='shopping_cart'),
    # path('shopping_cart_remove/', views.shopping_cart_remove, name='shopping_cart_remove'),


    path('manage_order/', views.manage_order, name='manage_order'),
    path('manage_vector/', views.manage_vector, name='manage_vector'),
    path('vector_add_file/', views.vector_add_file, name='vector_add_file'),
    path('vector_add_table/', views.vector_add_table, name='vector_add_table'),
    path('vector_detail/<int:vector_id>/', views.vector_detail, name='vector_detail'),
    path('vector_edit/<int:vector_id>/', views.vector_edit, name='vector_edit'),
    path('vector_delete/<int:vector_id>/', views.vector_delete, name='vector_delete'),
    path('vector_validation/<int:vector_id>/', views.vector_validation, name='vector_validation'),
    path('validation_save/<str:vector_or_gene>/<int:id>/', views.validation_save, name='validation_save'),
    path('vector_download/<int:vector_id>/<str:file_type>/', views.vector_download, name='vector_download'),
    # path('download_pdf/<int:order_id>/', views.download_pdf, name='download_pdf'),

]