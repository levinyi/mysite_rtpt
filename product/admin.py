from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

# Register your models here.
from .models import Product, Addon, ExpressionScale, ExpressionHost,PurificationMethod, Vector, GeneSynEnzymeCutSite, Species

class VectorResource(resources.ModelResource):
    class Meta:
        model = Vector
        fields = ('id', 'vector_id', 'vector_name', 'vector_map',  'NC5', 'NC3', 'iu20','id20')

class VectorAdmin(ImportExportModelAdmin):
    list_display = ('vector_name', 'create_date','id', 'user', 'vector_id', 'status', 'vector_file', 'vector_png')
    list_filter = ('vector_name', 'create_date','id', 'user', 'vector_id', 'status', 'vector_file')
    search_fields = ('vector_name', 'create_date','id', 'user', 'vector_id', 'status', 'vector_file')
    resource_class = VectorResource

class GeneSynEnzymeCutSiteAdmin(admin.ModelAdmin):
    list_display = ('enzyme_name', 'enzyme_seq', 'usescope')
    list_filter = ('enzyme_name', 'enzyme_seq', 'usescope')
    search_fields = ('enzyme_name', 'enzyme_seq', 'usescope')

class SpeciesResource(resources.ModelResource):
    class Meta:
        model = Species
        fields = ('id', 'species_name','species_note')

class SpeciesAdmin(ImportExportModelAdmin):
    list_display = ('id', 'species_name','species_note')
    list_filter = ('id', 'species_name',)
    search_fields = ('id', 'species_name',)
    resource_class = SpeciesResource

admin.site.register(Product)
admin.site.register(Addon)
admin.site.register(ExpressionHost)
admin.site.register(PurificationMethod)
admin.site.register(ExpressionScale)

admin.site.register(Vector, VectorAdmin)
admin.site.register(GeneSynEnzymeCutSite, GeneSynEnzymeCutSiteAdmin)
admin.site.register(Species, SpeciesAdmin)
