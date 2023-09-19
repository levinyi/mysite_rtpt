from django.contrib import admin
from .models import Order, ShoppingCart

# Register your models here.

class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'project_name', 'product', 'purification_method', 'express_host', 'scale', 'antibody_number', 'analysis', 'total_price')
    list_filter = ('user', 'status','project_name', 'product', 'purification_method', 'express_host', 'scale', 'antibody_number', 'analysis', 'total_price')
    search_fields = ('user', 'status','project_name', 'product', 'purification_method', 'express_host', 'scale', 'antibody_number', 'analysis', 'total_price')
    ordering = ('id',)

    

admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Order)