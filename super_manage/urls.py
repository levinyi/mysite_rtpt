from django.urls import path
from . import views

app_name = 'super_manage'

urlpatterns = [
    path('order_manage/', views.order_manage, name='order_manage'),
    path('vector_manage/', views.vector_manage, name='vector_manage'),
    path('order_manage/change_status/', views.change_status, name='change_status'),
    path('order_manage/change_url/', views.change_url, name='change_url'),
    path('get_rows', views.get_rows, name='get_rows'),
    path('order_manage/upload_report', views.upload_report, name='upload_report'),
    path('vector_manage/submit_vector_data', views.submit_vector_data, name='submit_vector_data'),
    path('vector_manage/vector_download/<int:vector_id>/<str:file_type>', views.vector_download, name='vector_download'),

    # added by dushiyi
    path('export_order_to_csv/<int:order_id>', views.export_order_to_csv, name='export_order_to_csv'),
]