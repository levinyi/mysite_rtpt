from django.urls import path
from . import views

app_name = 'tools'
urlpatterns = [
    path('tools-list/', views.tools_list, name='tools_list'),
    path('SequenceAnalyzer/', views.SequenceAnalyzer, name='SequenceAnalyzer'),
]