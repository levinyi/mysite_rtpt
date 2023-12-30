from django.urls import path
from . import views
from user_center.views import export_order_to_csv

app_name = 'super_manage'

urlpatterns = [
    path('order_manage/', views.order_manage, name='order_manage'),
    path('order_manage/change_status/', views.change_status, name='change_status'),
    path('order_manage/change_url/', views.change_url, name='change_url'),
    path('order_manage/upload_report', views.upload_report, name='upload_report'),
    path('order_manage/download_report/<int:order_id>', views.download_report, name='download_report'),
    path('order_manage/delete_report', views.delete_report, name='delete_report'),
    path('order_manage/export_order_to_csv/<int:order_id>', export_order_to_csv, name='export_order_to_csv'),

    path('vector_manage/', views.vector_manage, name='vector_manage'),
    path('vector_manage/submit_vector_data', views.submit_vector_data, name='submit_vector_data'),
    path('vector_manage/vector_download/<int:vector_id>/<str:file_type>', views.vector_download, name='vector_download'),
    path('vector_manage/vector_delete/', views.vector_delete, name='vector_delete'),
    path('vector_manage/vector_upload/', views.vector_upload, name='vector_upload'),

    path('get_rows', views.get_rows, name='get_rows'),

    # user management
    path('user_manage/', views.user_manage, name='user_manage'),
]