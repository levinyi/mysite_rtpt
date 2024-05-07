from django.urls import path
from . import views

app_name = 'product'
urlpatterns = [
    path('product_list/', views.product_list, name='product_list'),
    # path('create_order/', views.create_order, name='create_order'),
    path('order_selection/<int:order_id>/', views.order_selection, name='order_selection'),
    path('order_quotation/<int:order_id>/', views.order_quotation, name='order_quotation'),
    path('vector_validation/', views.vector_validation, name='vector_validation'),

    # for species
    path('upload_species_codon_file/', views.upload_species_codon_file, name='upload_species_codon_file'),
    path('species_delete/', views.species_delete, name='species_delete'),
]