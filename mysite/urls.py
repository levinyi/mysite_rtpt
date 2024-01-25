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
from django.views.generic import TemplateView

import data_process.views
from .views import HomeView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('', HomeView.as_view(), name='home'),
    path('account/', include('account.urls', namespace='account')),
    path('product/', include('product.urls', namespace='product')),
    path('user_center/', include('user_center.urls', namespace=' ')),
    path('tools/', include('tools.urls', namespace='tools')),
    path('super_manage/', include('super_manage.urls', namespace='super_manage')),
    path('data_process/request_genes', data_process.views.request_genes, name='request_genes'),
    path('data_process/upload_genes', data_process.views.upload_genes, name='upload_genes')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
