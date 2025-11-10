from django import forms
from phonenumber_field.formfields import PhoneNumberField
from .models import PhoneRequest

class PhoneRequestForm(forms.ModelForm):
    phone = PhoneNumberField(
        widget=forms.TextInput(
            attrs={ 
                'class': 'form-control',
                'placeholder': 'شماره تلفن را وارد کنید'
            }
        ),
        
        help_text='شماره تلفن را با کد کشور وارد کنید (مثال: **** 98 912 345 +)',
        label='شماره تلفن'
    )
    
    class Meta:
        model = PhoneRequest
        fields = ['phone']
    
    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if phone and not phone.is_valid():
            raise forms.ValidationError('شماره تلفن وارد شده معتبر نیست')
        
         # بررسی تکراری نبودن شماره تلفن
        if PhoneRequest.objects.filter(phone=phone).exists():
            raise forms.ValidationError('این شماره تلفن قبلاً ثبت شده است')
        
        return phone
    
class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        label='فایل اکسل',
        help_text='فایل اکسل حاوی شماره تلفن‌ها را انتخاب کنید (فرمت: xlsx یا xls)',
        widget=forms.FileInput(
            attrs={
                'class': 'form-control',
                'accept': '.xlsx,.xls'
            }
        )
    )
    
    def clean_excel_file(self):
        file = self.cleaned_data['excel_file']
        if file:
            # بررسی پسوند فایل
            if not file.name.endswith(('.xlsx', '.xls')):
                raise forms.ValidationError('فقط فایل‌های اکسل با فرمت xlsx یا xls مجاز هستند')
            
            # بررسی حجم فایل (حداکثر 5MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('حجم فایل نباید بیشتر از 5 مگابایت باشد')
        
        return file