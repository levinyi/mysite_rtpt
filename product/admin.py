from django.contrib import admin

# Register your models here.
from .models import Product, Addon, ExpressionScale, ExpressionHost,PurificationMethod, Vector, GeneSynEnzymeCutSite


class VectorAdmin(admin.ModelAdmin):
    list_display = ('vector_name', 'status')
    list_filter = ('vector_name', 'status')
    search_fields = ('vector_name', 'status')

class GeneSynEnzymeCutSiteAdmin(admin.ModelAdmin):
    list_display = ('enzyme_name', 'enzyme_seq', 'usescope')
    list_filter = ('enzyme_name', 'enzyme_seq', 'usescope')
    search_fields = ('enzyme_name', 'enzyme_seq', 'usescope')

admin.site.register(Product)
admin.site.register(Addon)
admin.site.register(ExpressionHost)
admin.site.register(PurificationMethod)
admin.site.register(ExpressionScale)
admin.site.register(Vector, VectorAdmin)
admin.site.register(GeneSynEnzymeCutSite, GeneSynEnzymeCutSiteAdmin)
