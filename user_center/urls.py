from django.urls import path
from . import views

app_name = 'user_center'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('order_create/', views.order_create, name='order_create'),
    # gene
    # path('gene_detail_old/', views.gene_detail_old, name='gene_detail_old'),
    path('gene_detail/', views.gene_detail, name='gene_detail'),
    path('gene_data_api/', views.gene_data_api, name='gene_data_api'),
    path('save_species/', views.save_species, name='save_species'),
    path('gene_edit/<int:gene_id>/', views.gene_edit, name='gene_edit'),
    # path('protein_edit/<int:gene_id>/', views.protein_edit, name='protein_edit'),
    path('gene_delete/', views.gene_delete, name='gene_delete'),
    path('gene_validation/', views.gene_validation, name='gene_validation'),
    path('bulk_optimization_submit/', views.bulk_optimization_submit, name='bulk_optimization_submit'),
    path('bulk_optimization_display/', views.bulk_optimization_display, name='bulk_optimization_display'),
    path('condon_optimization_api/', views.condon_optimization_api, name='condon_optimization_api'),

    # shopping cart
    path('view_cart/', views.view_cart, name='view_cart'),
    path('cart_genbank_download/<int:gene_id>/', views.cart_genbank_download, name='cart_genbank_download'),
    path('bulk_download_genbank/', views.bulk_download_genbank, name='bulk_download_genbank'),
    path('bulk_download_geneinfo_excel/', views.bulk_download_geneinfo_excel, name='bulk_download_geneinfo_excel'),
    path('bulk_view_gene_detail/', views.bulk_view_gene_detail, name='bulk_view_gene_detail'),
    path('checkout/', views.checkout, name='checkout'),
    path('submit_notification/', views.submit_notification, name='submit_notification'),

    # order
    path('manage_order/', views.manage_order, name='manage_order'),
    path('view_order_detail/<int:order_id>/', views.view_order_detail, name='view_order_detail'),
    path('export_order_to_csv/<int:order_id>/', views.export_order_to_csv, name='export_order_to_csv'),
    path('order_delete/', views.order_delete, name='order_delete'),
    # vector
    path('manage_vector/', views.manage_vector, name='manage_vector'),
    path('customer_vector_data_api/', views.customer_vector_data_api, name='customer_vector_data_api'),
    path('rootpath_vector_data_api/', views.rootpath_vector_data_api, name='rootpath_vector_data_api'),

    path('vector_upload/', views.vector_upload, name='vector_upload'),
    path('vector_delete/', views.vector_delete, name='vector_delete'),
    path('validation_save/<int:id>/', views.validation_save, name='validation_save'),
    path('vector_download/<int:vector_id>/<str:file_type>/', views.vector_download, name='vector_download'),

    # api
    path('api/generate-genbank/', views.generate_genbank, name='generate_genbank'),
    path('test/', views.test, name='test'),
]