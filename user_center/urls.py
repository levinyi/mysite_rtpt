from django.urls import path
from . import views

app_name = 'user_center'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('order_create/', views.order_create, name='order_create'),
    path('gene_detail/', views.gene_detail, name='gene_detail'),
    path('save_species/', views.save_species, name='save_species'),
    path('gene_edit/<int:gene_id>/', views.gene_edit, name='gene_edit'),
    path('protein_edit/<int:gene_id>/', views.protein_edit, name='protein_edit'),
    path('gene_delete/', views.gene_delete, name='gene_delete'),
    path('gene_validation/', views.gene_validation, name='gene_validation'),
    path('view_cart/', views.view_cart, name='view_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('submit_notification/', views.submit_notification, name='submit_notification'),
    path('manage_order/', views.manage_order, name='manage_order'),


    path('manage_vector/', views.manage_vector, name='manage_vector'),
    path('vector_upload/', views.vector_upload, name='vector_upload'),
    path('vector_delete/', views.vector_delete, name='vector_delete'),
    path('validation_save/<int:id>/', views.validation_save, name='validation_save'),
    path('vector_download/<int:vector_id>/<str:file_type>/', views.vector_download, name='vector_download'),

    # path('vector_add_file/', views.vector_add_file, name='vector_add_file'),
    # path('vector_add_table/', views.vector_add_table, name='vector_add_table'),
    # path('vector_detail/<int:vector_id>/', views.vector_detail, name='vector_detail'),
    # path('vector_edit/<int:vector_id>/', views.vector_edit, name='vector_edit'),
    # path('vector_validation/<int:vector_id>/', views.vector_validation, name='vector_validation'),
]