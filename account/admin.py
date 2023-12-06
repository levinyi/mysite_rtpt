from django.contrib import admin
from .models import UserProfile
from import_export import resources
from import_export.admin import ImportExportModelAdmin


# Register your models here.

class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'first_name', 'last_name', 'company', 'address', 'city', 'state', 'zip_code', 'country', 'phone_number', 'email')
    list_filter = ('user', 'first_name', 'last_name', 'company', 'address', 'city', 'state', 'zip_code', 'country', 'phone_number', 'email')
    search_fields = ('user', 'first_name', 'last_name', 'company', 'address', 'city', 'state', 'zip_code', 'country', 'phone_number', 'email')
    ordering = ('id',)

class UserProfilereSource(resources.ModelResource):
    class Meta:
        model = UserProfile
        fields = ('user','first_name', 'last_name','email','company','department', 'phone', 'register_time', 'shipping_address')

class UserProfileAdmin(ImportExportModelAdmin):
    list_display = ('id','user','first_name', 'last_name','email','company','department', 'phone', 'register_time', 'shipping_address')
    list_filter = ('id','user','first_name', 'last_name','email','company','department', 'phone', 'register_time')
    search_fields = ('id','user','first_name', 'last_name','email','company','department', 'phone', 'register_time')
    resource_class = UserProfilereSource

# admin.site.register(Account)
admin.site.register(UserProfile,UserProfileAdmin)
