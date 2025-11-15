from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from extensions.utils import jalali_converter
from django.utils import timezone


class PhoneRequest(models.Model):
    # is_processed = models.BooleanField(default=False)  # آیا پردازش شده؟
    phone = PhoneNumberField(blank=True, null=True, verbose_name='شماره تلفن')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.phone) if self.phone else f"درخواست {self.id}"

    def jinfo(self):
        return jalali_converter(self.created_at)
    jinfo.short_description = 'تاریخ درخواست'
     

    class Meta:
        ordering = ['-created_at'] 
        verbose_name = 'درخواست شماره تلفن'
        verbose_name_plural = 'درخواست‌های شماره تلفن'


class UserData(models.Model):
    phone_request = models.ForeignKey(PhoneRequest, on_delete=models.CASCADE, related_name='user_data')  # ارتباط با درخواست
    user_name = models.CharField(max_length=200, verbose_name='نام کاربری')
    telegram_Id = models.TextField(verbose_name='ایدی تلگرام')
    image_link = models.URLField(max_length=500)  
    created_at = models.DateTimeField(auto_now_add=True)
  
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'داده کاربر'
        verbose_name_plural = 'داده‌های کاربران'
        

class SherlockSearch(models.Model):
    username = models.CharField(max_length=100, verbose_name='نام کاربری')
    search_date = models.DateTimeField(default=timezone.now, verbose_name='تاریخ جستجو')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'در حال جستجو'),
            ('completed', 'تکمیل شده'),
            ('failed', 'ناموفق')
        ],
        default='pending',
        verbose_name='وضعیت'
    )
    results = models.JSONField(null=True, blank=True, verbose_name='نتایج')
    total_found = models.IntegerField(default=0, verbose_name='تعداد یافت شده')
    
    def __str__(self):
        return f"{self.username} - {self.search_date.jinfo}"
    
    def jinfo(self):
        return jalali_converter(self.search_date)
    jinfo.short_description = 'تاریخ درخواست'
    
    class Meta:
        ordering = ['-search_date']
        verbose_name = 'جستجوی شرلوک'
        verbose_name_plural = 'جستجوهای شرلوک'
    
    