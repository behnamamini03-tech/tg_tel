from django.contrib import admin
from .models import PhoneRequest, UserData



@admin.register(PhoneRequest)
class PhoneRequestAdmin(admin.ModelAdmin):
    list_display = ('phone', 'created_at', 'id')
    list_filter = ('created_at',)
    search_fields = ('phone',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('اطلاعات درخواست', {
            'fields': ('phone', 'created_at')
        }),
    )
    
    def has_add_permission(self, request):
        # اختیاری: محدود کردن اضافه کردن از پنل ادمین
        return True
    
    def has_change_permission(self, request, obj=None):
        # اختیاری: محدود کردن ویرایش از پنل ادمین
        return True

@admin.register(UserData)
class UserDataAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'telegram_Id', 'created_at', 'id')
    list_filter = ('created_at',)
    search_fields = ('user_name', 'telegram_Id')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user_name', 'telegram_Id', 'image_link')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # غیرفعال کردن افزودن رکورد جدید
        return False
    
    def has_delete_permission(self, request, obj=None):
        # اختیاری: کنترل دسترسی حذف
        return request.user.is_superuser

