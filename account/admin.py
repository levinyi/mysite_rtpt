from django.contrib import admin
from .models import Account, UserProfile


# Register your models here.

class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'first_name', 'last_name', 'company', 'address', 'city', 'state', 'zip_code', 'country', 'phone_number', 'email')
    list_filter = ('user', 'first_name', 'last_name', 'company', 'address', 'city', 'state', 'zip_code', 'country', 'phone_number', 'email')
    search_fields = ('user', 'first_name', 'last_name', 'company', 'address', 'city', 'state', 'zip_code', 'country', 'phone_number', 'email')
    ordering = ('id',)


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id','user','user')

admin.site.register(Account)
admin.site.register(UserProfile,UserProfileAdmin)
