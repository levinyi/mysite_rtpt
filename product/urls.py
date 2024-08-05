from django.urls import path
from . import views

app_name = 'product'
urlpatterns = [
    path('vector_validation/', views.vector_validation, name='vector_validation'),

    # for species
    path('upload_species_codon_file/', views.upload_species_codon_file, name='upload_species_codon_file'),
    path('species_delete/', views.species_delete, name='species_delete'),
]