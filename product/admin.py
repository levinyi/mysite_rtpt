import re

from django import forms
from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

# Register your models here.
from .models import Vector, GeneSynEnzymeCutSite, Species

class VectorResource(resources.ModelResource):
    class Meta:
        model = Vector
        fields = ('id', 'user', 'vector_id', 'vector_name', 'vector_map', 'NC5', 'NC3', 'iu20', 'id20',
                  'i5NC', 'i3NC', 'cloning_method', 'modify_vector', 'antibiotic_resistance', 'design_status',
                  'design_error', 'primer_forward', 'primer_reverse', 'primer_forward_tm',
                  'primer_reverse_tm', 'backbone_primer_forward', 'backbone_primer_reverse',
                  'create_date', 'status')

IUPAC_BASES_RE = re.compile(r'^[ACGTURYSWKMBDHVN]+$', re.IGNORECASE)


class VectorAdminForm(forms.ModelForm):
    """iU20/iD20 必须恰好 20 bp：少填/多填一个碱基会让插入位点定位悄悄出错，很难排查。"""

    class Meta:
        model = Vector
        fields = '__all__'

    def _clean_site_20bp(self, field, label):
        value = self.cleaned_data.get(field)
        if not value:
            return value
        seq = re.sub(r'\s+', '', value)
        if not IUPAC_BASES_RE.match(seq):
            bad = sorted(set(c for c in seq if not IUPAC_BASES_RE.match(c)))
            raise forms.ValidationError(f"{label} 含非碱基字符：{' '.join(bad)}")
        if len(seq) != 20:
            raise forms.ValidationError(f"{label} 必须是 20 bp，当前为 {len(seq)} bp")
        return seq

    def clean_iu20(self):
        return self._clean_site_20bp('iu20', 'iU20')

    def clean_id20(self):
        return self._clean_site_20bp('id20', 'iD20')


class VectorAdmin(ImportExportModelAdmin):
    form = VectorAdminForm
    list_display = ('id', 'vector_name', 'user', 'vector_id', 'cloning_method', 'modify_vector',
                    'antibiotic_resistance',
                    'design_status', 'status', 'create_date', 'vector_file', 'vector_png')
    list_filter = ('user', 'cloning_method', 'modify_vector', 'antibiotic_resistance', 'design_status',
                   'status', 'create_date')
    search_fields = ('vector_name', 'vector_id', 'user__username', 'user__email')
    readonly_fields = ('create_date', 'primer_forward_tm', 'primer_reverse_tm',
                       'backbone_primer_forward_tm', 'backbone_primer_reverse_tm')
    resource_class = VectorResource

    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'vector_id', 'vector_name', 'status', 'create_date')
        }),
        ('序列信息', {
            'fields': ('vector_map', 'NC5', 'NC3', 'iu20', 'id20', 'i5NC', 'i3NC')
        }),
        ('载体改造设计', {
            'fields': ('cloning_method', 'modify_vector', 'antibiotic_resistance', 'design_status',
                      'design_error',
                      'primer_forward', 'primer_reverse', 'primer_forward_tm', 'primer_reverse_tm')
        }),
        ('骨架PCR引物（不改造模式）', {
            'fields': ('backbone_primer_forward', 'backbone_primer_reverse',
                      'backbone_primer_forward_tm', 'backbone_primer_reverse_tm'),
            'classes': ('collapse',),
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
