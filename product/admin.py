from django.contrib import admin

# Register your models here.
from .models import Product, Addon, ExpressionScale, ExpressionHost,PurificationMethod, Vector, GeneSynEnzymeCutSite, Species


class VectorAdmin(admin.ModelAdmin):
    list_display = ('vector_name', 'user', 'status')
    list_filter = ('vector_name', 'user', 'status')
    search_fields = ('vector_name', 'user', 'status')

class GeneSynEnzymeCutSiteAdmin(admin.ModelAdmin):
    list_display = ('enzyme_name', 'enzyme_seq', 'usescope')
    list_filter = ('enzyme_name', 'enzyme_seq', 'usescope')
    search_fields = ('enzyme_name', 'enzyme_seq', 'usescope')

class SpeciesAdmin(admin.ModelAdmin):
    list_display = ('species_name',)
    list_filter = ('species_name',)
    search_fields = ('species_name',)

admin.site.register(Product)
admin.site.register(Addon)
admin.site.register(ExpressionHost)
admin.site.register(PurificationMethod)
admin.site.register(ExpressionScale)
admin.site.register(Vector, VectorAdmin)
admin.site.register(GeneSynEnzymeCutSite, GeneSynEnzymeCutSiteAdmin)
admin.site.register(Species, SpeciesAdmin)
