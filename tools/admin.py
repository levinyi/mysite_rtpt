from django.contrib import admin
from .models import Tool
# Register your models here.

@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ('tool_name', 'name_alias', 'tool_desc', 'tool_freq', 'icon')
    search_fields = ('tool_name', 'tool_desc', 'tool_freq')
    list_filter = ('tool_name', 'tool_freq')