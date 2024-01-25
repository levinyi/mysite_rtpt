from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'account'
urlpatterns = [
    path('login/', views.custom_login_required(auth_views.LoginView.as_view(template_name='account/login.html')), name='user_login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='account/logout.html'), name='user_logout'),
    # path('logout/', views.user_logout, name='user_logout'),
    path('register/', views.register, name='user_register'),
    path('register_confirm/', views.register_confirm, name='register_confirm'),
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='account/password_change_form.html', success_url='/account/password-change-done/'), name='password_change'),
    path('password-change-done/', auth_views.PasswordChangeDoneView.as_view(template_name='account/password_change_done.html'), name='password_change_done'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='account/password_reset_form.html', email_template_name='account/password_reset_email.html', subject_template_name='account/password_reset_subject.txt', success_url='/account/password-reset-done/'), name='password_reset'),
    path('password-reset-done/', auth_views.PasswordResetDoneView.as_view(template_name='account/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', views.custom_password_reset_confirm, name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='account/password_reset_complete.html'), name='password_reset_complete'),

    path('verify/<uidb64>/<token>/', views.verify, name='verify'),
    path('resend_login_verify/<str:username>/<str:verify_type>', views.resend_login_verify, name='resend_login_verify'),
    path('email_not_verify/', views.email_not_verify, name='email_not_verify'),
    path('phone_not_verify/', views.phone_not_verify, name='phone_not_verify'),
    path('forgot_passwd/', views.forgot_passwd, name='forgot_passwd'),

    path('my-information/', views.myself, name='my_information'),
    path('myself_edit/', views.myself_edit, name='myself_edit'),
    path('avatar_edit/', views.avatar_edit, name='avatar_edit'),

    path('settings/', views.settings, name='settings'),
    path('contact_us/', views.contact_us, name='contact_us'),
]