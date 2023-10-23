from django.contrib import admin
from .models import Tool
# Register your models here.

class ToolAdmin(admin.ModelAdmin):
    list_display = ('tool_name', 'tool_desc', 'tool_freq', 'tool_icon')
    search_fields = ('tool_name', 'tool_desc', 'tool_freq', 'tool_icon')
    list_filter = ('tool_name', 'tool_desc', 'tool_freq', 'tool_icon') 

admin.site.register(Tool, ToolAdmin)