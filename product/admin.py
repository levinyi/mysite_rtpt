from django.contrib import admin

# Register your models here.
from .models import Product, Addon, ExpressionScale, ExpressionHost,PurificationMethod

admin.site.register(Product)
admin.site.register(Addon)
admin.site.register(ExpressionHost)
admin.site.register(PurificationMethod)
admin.site.register(ExpressionScale)
