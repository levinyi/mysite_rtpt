from django.contrib import admin
from .models import GeneInfo, OrderInfo, Cart, ProcessTask
from import_export import resources
from import_export.admin import ImportExportModelAdmin

# Register your models here.
class GeneInfoResource(resources.ModelResource):
    class Meta:
        model = GeneInfo
        fields = ('id', 'user', 'gene_name', 'original_seq', 'combined_seq', 'saved_seq', 'vector', 'species',
                  'status', 'create_date', 'forbid_seq', 'forbidden_check_list', 'contained_forbidden_list',
                  'i5nc', 'i3nc', 'original_gc_content', 'modified_gc_content', 'penalty_score',
                  'seq_type', 'optimization_id', 'optimization_method', 'optimization_status',
                  'restriction_decision', 'restriction_process_route', 'bsai_count', 'bsmbi_count')
class GeneInfoAdmin(ImportExportModelAdmin):
    list_display = ('id', 'gene_name', 'user', 'vector', 'species', 'status', 'seq_type',
                    'optimization_status', 'restriction_decision', 'penalty_score', 'create_date')
    list_filter = ('user', 'vector', 'species', 'status', 'seq_type', 'optimization_status',
                   'restriction_decision', 'restriction_process_route', 'restriction_requires_manual_review',
                   'create_date')
    search_fields = ('gene_name', 'user__username', 'user__email', 'optimization_id')
    readonly_fields = ('create_date', 'original_gc_content', 'modified_gc_content', 'penalty_score',
                      'bsai_count', 'bsmbi_count')
    resource_class = GeneInfoResource

    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'gene_name', 'vector', 'species', 'status', 'create_date')
        }),
        ('序列信息', {
            'fields': ('seq_type', 'original_seq', 'combined_seq', 'saved_seq', 'i5nc', 'i3nc',
                      'original_gc_content', 'modified_gc_content', 'penalty_score')
        }),
        ('优化信息', {
            'fields': ('optimization_id', 'optimization_method', 'optimization_status', 'optimization_message')
        }),
        ('限制性酶切位点', {
            'fields': ('restriction_decision', 'restriction_process_route', 'restriction_message',
                      'restriction_requires_manual_review', 'bsai_count', 'bsmbi_count',
                      'bsai_positions', 'bsmbi_positions')
        }),
        ('禁用序列检查', {
            'fields': ('forbid_seq', 'forbidden_check_list', 'contained_forbidden_list')
        }),
        ('高级数据', {
            'fields': ('original_highlights', 'modified_highlights', 'analysis_results', 'fragments_data'),
            'classes': ('collapse',)
        }),
    )


class OrderInfoResource(resources.ModelResource):
    class Meta:
        model = OrderInfo
        fields = ('id', 'user', 'inquiry_id', 'order_time', 'status', 'url', 'report_file')

class OrderInfoAdmin(ImportExportModelAdmin):
    list_display = ('id', 'user', 'inquiry_id', 'order_time', 'status', 'report_file')
    list_filter = ('user', 'status', 'order_time')
    search_fields = ('id', 'inquiry_id', 'user__username', 'user__email')
    readonly_fields = ('order_time',)
    filter_horizontal = ('gene_infos',)
    resource_class = OrderInfoResource

    fieldsets = (
        ('订单信息', {
            'fields': ('user', 'inquiry_id', 'order_time', 'status')
        }),
        ('基因信息', {
            'fields': ('gene_infos',)
        }),
        ('报告', {
            'fields': ('url', 'report_file')
        }),
    )

class ProcessTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_id', 'user', 'vector', 'species', 'status', 'progress', 'total',
                    'get_progress_percentage', 'created_at', 'completed_at')
    list_filter = ('status', 'vector', 'species', 'created_at', 'user')
    search_fields = ('task_id', 'user__username', 'user__email')
    readonly_fields = ('task_id', 'created_at', 'updated_at', 'completed_at', 'get_progress_percentage')

    fieldsets = (
        ('任务信息', {
            'fields': ('task_id', 'user', 'vector', 'species', 'status')
        }),
        ('进度信息', {
            'fields': ('progress', 'total', 'get_progress_percentage')
        }),
        ('结果信息', {
            'fields': ('gene_ids', 'error_message')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )

    def get_progress_percentage(self, obj):
        return f"{obj.get_progress_percentage()}%"
    get_progress_percentage.short_description = '完成百分比'

class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at')
    list_filter = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('genes',)

    fieldsets = (
        ('购物车信息', {
            'fields': ('user', 'created_at', 'updated_at')
        }),
        ('基因列表', {
            'fields': ('genes',)
        }),
    )

admin.site.register(GeneInfo, GeneInfoAdmin)
admin.site.register(OrderInfo, OrderInfoAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(ProcessTask, ProcessTaskAdmin)