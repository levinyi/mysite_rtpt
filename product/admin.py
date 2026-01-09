from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

# Register your models here.
from .models import Vector, GeneSynEnzymeCutSite, Species

class VectorResource(resources.ModelResource):
    class Meta:
        model = Vector
        fields = ('id', 'user', 'vector_id', 'vector_name', 'vector_map', 'NC5', 'NC3', 'iu20', 'id20',
                  'i5NC', 'i3NC', 'cloning_method', 'antibiotic_resistance', 'design_status',
                  'design_error', 'primer_forward', 'primer_reverse', 'primer_forward_tm',
                  'primer_reverse_tm', 'create_date', 'status')

class VectorAdmin(ImportExportModelAdmin):
    list_display = ('id', 'vector_name', 'user', 'vector_id', 'cloning_method', 'antibiotic_resistance',
                    'design_status', 'status', 'create_date', 'vector_file', 'vector_png')
    list_filter = ('user', 'cloning_method', 'antibiotic_resistance', 'design_status', 'status', 'create_date')
    search_fields = ('vector_name', 'vector_id', 'user__username', 'user__email')
    readonly_fields = ('create_date', 'primer_forward_tm', 'primer_reverse_tm')
    resource_class = VectorResource

    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'vector_id', 'vector_name', 'status', 'create_date')
        }),
        ('序列信息', {
            'fields': ('vector_map', 'NC5', 'NC3', 'iu20', 'id20', 'i5NC', 'i3NC')
        }),
        ('载体改造设计', {
            'fields': ('cloning_method', 'antibiotic_resistance', 'design_status', 'design_error',
                      'primer_forward', 'primer_reverse', 'primer_forward_tm', 'primer_reverse_tm')
        }),
        ('文件', {
            'fields': ('vector_file', 'vector_png', 'vector_gb')
        }),
    )

class GeneSynEnzymeCutSiteAdmin(admin.ModelAdmin):
    list_display = ('enzyme_name', 'enzyme_seq', 'usescope')
    list_filter = ('enzyme_name', 'enzyme_seq', 'usescope')
    search_fields = ('enzyme_name', 'enzyme_seq', 'usescope')

class SpeciesResource(resources.ModelResource):
    class Meta:
        model = Species
        fields = ('id', 'species_name', 'species_note', 'species_codon_file')

class SpeciesAdmin(ImportExportModelAdmin):
    list_display = ('id', 'species_name', 'species_note', 'species_codon_file')
    list_filter = ('species_name',)
    search_fields = ('species_name', 'species_note')
    resource_class = SpeciesResource

    fieldsets = (
        ('物种信息', {
            'fields': ('species_name', 'species_note')
        }),
        ('密码子文件', {
            'fields': ('species_codon_file',)
        }),
    )


admin.site.register(Vector, VectorAdmin)
admin.site.register(GeneSynEnzymeCutSite, GeneSynEnzymeCutSiteAdmin)
admin.site.register(Species, SpeciesAdmin)
