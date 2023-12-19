from django.contrib import admin
from .models import Notice
# Register your models here.

class NoticeAdmin(admin.ModelAdmin):
    list_display = ('user','token', 'purpose', 'verify_type', 'create_time', 'expired_time', 'code', 'used')
    list_filter = ('user','token', 'purpose', 'verify_type', 'create_time', 'expired_time', 'code', 'used')
    search_fields = ('user','token', 'purpose', 'verify_type', 'create_time', 'expired_time', 'code', 'used')


admin.site.register(Notice, NoticeAdmin)