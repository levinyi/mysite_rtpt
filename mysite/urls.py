"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from .views import HomeView
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language
from . import views

urlpatterns = [
    path('switch_language/', views.switch_language, name='switch_language'),  # 如果你需要这个自定义语言切换视图
    path('set_language/', set_language, name='set_language'),  # 设置语言
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('accounts/', include('allauth.urls')),  # 登录和注册使用的是 allauth
    path('user_account/', include('user_account.urls', namespace='user_account')),
    path('product/', include('product.urls', namespace='product')),
    path('user_center/', include('user_center.urls', namespace='user_center')),
    path('tools/', include('tools.urls', namespace='tools')),
    path('super_manage/', include('super_manage.urls', namespace='super_manage')),
]
# 添加静态和媒体文件路由（不要包含在 i18n_patterns 中）
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
