from django.contrib import admin
from .models import GeneInfo, OrderInfo, Cart

# Register your models here.
admin.site.register(GeneInfo)
admin.site.register(OrderInfo)
admin.site.register(Cart)