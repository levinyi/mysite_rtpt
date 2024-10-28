from django.urls import path
from . import views
from user_center.views import export_order_to_csv

app_name = 'super_manage'

urlpatterns = [
    path('order_manage/', views.order_manage, name='order_manage'),
    path('order_data_api/', views.order_data_api, name='order_data_api'),
    path('order_manage_old/', views.order_manage_old, name='order_manage_old'),

    path('order_manage/change_status/', views.change_status, name='change_status'),
    path('order_manage/change_url/', views.change_url, name='change_url'),
    path('order_manage/upload_report/', views.upload_report, name='upload_report'),
    path('order_manage/download_report/<int:order_id>/', views.download_report, name='download_report'),
    path('order_manage/delete_report/', views.delete_report, name='delete_report'),
    path('order_manage/export_order_to_csv/<int:order_id>/', export_order_to_csv, name='export_order_to_csv'),
    path('order_to_reqins/<int:order_id>/', views.order_to_reqins, name='order_to_reqins'),

    path('vector_manage/', views.vector_manage, name='vector_manage'),
    path('vector_data_api/', views.vector_data_api, name='vector_data_api'),
    path('vector_manage_old/', views.vector_manage_old, name='vector_manage_old'),
    path('vector_manage/submit_vector_data/', views.submit_vector_data, name='submit_vector_data'),  # old?
    path('vector_manage/vector_update_field/', views.vector_update_field, name='vector_update_field'), # new
    path('vector_manage/vector_download/<int:vector_id>/<str:file_type>', views.vector_download, name='vector_download'),
    path('vector_manage/vector_delete/', views.vector_delete, name='vector_delete'),
    path('vector_manage/vector_upload/', views.vector_upload, name='vector_upload'),

    path('vector_upload_file/', views.vector_upload_file, name='vector_upload_file'),
    path('vector_add_item/', views.vector_add_item, name='vector_add_item'),
    path('vector_edit_item/', views.vector_edit_item, name='vector_edit_item'),

    path('get_rows', views.get_rows, name='get_rows'),

    # user management
    path('user_manage_old/', views.user_manage_old, name='user_manage_old'),
    path('user_manage/', views.user_manage, name='user_manage'),
    path('user_data_api/', views.user_data_api, name='user_data_api'),

    path('view_user_profile/<str:user_id>/', views.view_user_profile, name='view_user_profile'),
    path('save_user_profile/<str:user_id>/', views.save_user_profile, name='save_user_profile'),
    path('save_user_avatar/', views.save_user_avatar, name='save_user_avatar'),

    # species management
    path('species_manage_old/', views.species_manage_old, name='species_manage_old'),
    path('species_manage/', views.species_manage, name='species_manage'),
    path('species_data_api/', views.species_data_api, name='species_data_api'),
]