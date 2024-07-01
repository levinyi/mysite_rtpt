from django.urls import path
from . import views

app_name = 'tools'
urlpatterns = [
    path('tools-list/', views.tools_list, name='tools_list'),
    path('SequenceAnalyzer/', views.SequenceAnalyzer, name='SequenceAnalyzer'),
    path('sequence_analysis_detail/', views.sequence_analysis_detail, name='sequence_analysis_detail'),
    path('download_gene_table/', views.download_gene_table, name='download_gene_table'),

    # 2
    path('GenePlateExplorer/', views.GenePlateExplorer, name='GenePlateExplorer'),
    path('plate_view/', views.plate_view, name='plate_view'),


    # test
    path('test/', views.test, name='test'),
]