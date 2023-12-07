from django.contrib import admin
from .models import GeneInfo, OrderInfo, Cart
from import_export import resources
from import_export.admin import ImportExportModelAdmin

# Register your models here.
class GeneInfoResource(resources.ModelResource):
    class Meta:
        model = GeneInfo
        fields = ('id', 'user', 'gene_name', 'original_seq', 'vector', 'species', 'status', 'create_date', 'forbid_seq', 
                  'combined_seq', 'saved_seq', 'gc_content', 'forbidden_check_list', 'contained_forbidden_list')
class GeneInfoAdmin(ImportExportModelAdmin):
    list_display = ('id', 'user', 'gene_name', 'vector', 'species', 'status', 'create_date')
    list_filter = ('id', 'user', 'gene_name', 'vector', 'species', 'status', 'create_date')
    search_fields = ('id', 'user', 'gene_name', 'vector', 'species', 'status', 'create_date')
    resource_class = GeneInfoResource


class OrderInfoResource(resources.ModelResource):
    class Meta:
        model = OrderInfo
        fields = ('id', 'user', 'gene_infos', 'order_time', 'status')

class OrderInfoAdmin(ImportExportModelAdmin):
    list_display = ('id', 'user', 'inquiry_id', 'order_time', 'status')
    list_filter = ('id', 'user', 'order_time', 'status')
    search_fields = ('id', 'user', 'order_time', 'status')
    resource_class = OrderInfoResource

admin.site.register(GeneInfo, GeneInfoAdmin)
admin.site.register(OrderInfo, OrderInfoAdmin)
admin.site.register(Cart)