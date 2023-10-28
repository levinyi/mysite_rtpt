from django.contrib import admin

# Register your models here.
from .models import Product, Addon, ExpressionScale, ExpressionHost,PurificationMethod, Vector, GeneSynEnzymeCutSite


class VectorAdmin(admin.ModelAdmin):
    list_display = ('vector_name', 'status', 'NC5', 'NC3')
    list_filter = ('vector_name', 'status', 'NC5', 'NC3')
    search_fields = ('vector_name', 'status', 'NC5', 'NC3')


admin.site.register(Product)
admin.site.register(Addon)
admin.site.register(ExpressionHost)
admin.site.register(PurificationMethod)
admin.site.register(ExpressionScale)
admin.site.register(Vector, VectorAdmin)
admin.site.register(GeneSynEnzymeCutSite)
