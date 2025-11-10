from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncMonth
import json
import subprocess
from .forms import PhoneRequestForm, ExcelUploadForm
from .models import PhoneRequest, UserData
import pandas as pd
import phonenumbers
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import SherlockSearch
from .sherlock_utils import run_sherlock_search
from phonenumbers import NumberParseException
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from pathlib import Path

def phone_request_view(request):
    phone_form = PhoneRequestForm()
    excel_form = ExcelUploadForm()
    
    if request.method == 'POST':
        # بررسی اینکه کدام فرم ارسال شده
        if 'phone_submit' in request.POST:
            phone_form = PhoneRequestForm(request.POST)
            if phone_form.is_valid():
                phone_form.save()
                messages.success(request, 'شماره تلفن با موفقیت ثبت شد!')
                return redirect('app:phone_request')
        
        elif 'excel_submit' in request.POST:
            excel_form = ExcelUploadForm(request.POST, request.FILES)
            if excel_form.is_valid():
                excel_file = request.FILES['excel_file']
                
                try:
                    # خواندن فایل اکسل
                    df = pd.read_excel(excel_file)
                    
                    # بررسی وجود ستون شماره تلفن
                    phone_column = None
                    for col in df.columns:
                        if 'phone' in col.lower() or 'شماره' in col.lower() or 'تلفن' in col.lower():
                            phone_column = col
                            break
                    
                    if phone_column is None:
                        messages.error(request, 'ستون شماره تلفن در فایل اکسل یافت نشد. لطفاً ستونی با نام "phone" یا "شماره" ایجاد کنید.')
                        return redirect('app:phone_request')
                    
                    # پردازش شماره‌ها
                    success_count = 0
                    duplicate_count = 0
                    error_count = 0
                    errors = []
                    
                    for index, row in df.iterrows():
                        phone_value = str(row[phone_column]).strip()
                        
                        if pd.isna(row[phone_column]) or phone_value == '' or phone_value == 'nan':
                            continue
                        
                        try:
                            # تبدیل شماره به فرمت استاندارد
                            # اگر شماره با 0 شروع می‌شود، کد کشور ایران را اضافه کن
                            if phone_value.startswith('0'):
                                phone_value = '+98' + phone_value[1:]
                            elif not phone_value.startswith('+'):
                                phone_value = '+98' + phone_value
                            
                            # اعتبارسنجی شماره
                            parsed_phone = phonenumbers.parse(phone_value, None)
                            if not phonenumbers.is_valid_number(parsed_phone):
                                error_count += 1
                                errors.append(f'ردیف {index + 2}: شماره نامعتبر - {phone_value}')
                                continue
                            
                            # بررسی تکراری نبودن
                            formatted_phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
                            if PhoneRequest.objects.filter(phone=formatted_phone).exists():
                                duplicate_count += 1
                                continue
                            
                            # ذخیره شماره
                            PhoneRequest.objects.create(phone=formatted_phone)
                            success_count += 1
                            
                        except (NumberParseException, ValueError) as e:
                            error_count += 1
                            errors.append(f'ردیف {index + 2}: خطا در پردازش - {phone_value}')
                    
                    # نمایش نتایج
                    if success_count > 0:
                        messages.success(request, f'{success_count} شماره تلفن با موفقیت ثبت شد!')
                    if duplicate_count > 0:
                        messages.warning(request, f'{duplicate_count} شماره تکراری نادیده گرفته شد.')
                    if error_count > 0:
                        messages.error(request, f'{error_count} شماره نامعتبر یافت شد.')
                        for error in errors[:5]:  # نمایش 5 خطای اول
                            messages.error(request, error)
                    
                    return redirect('app:phone_request')
                    
                except Exception as e:
                    messages.error(request, f'خطا در پردازش فایل اکسل: {str(e)}')
                    return redirect('app:phone_request')
    
    context = {
        'phone_form': phone_form,
        'excel_form': excel_form
    }
    return render(request, 'registration/phone_request.html', context)


def phone_history_view(request):
    # دریافت تمام شماره‌ها به ترتیب جدیدترین
    phone_list = PhoneRequest.objects.all().order_by('-created_at')
    
    # جستجو
    search_query = request.GET.get('search', '')
    if search_query:
        phone_list = phone_list.filter(phone__icontains=search_query)
    
    # صفحه‌بندی - 20 آیتم در هر صفحه
    paginator = Paginator(phone_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # آمار کلی
    total_phones = PhoneRequest.objects.count()
    
    context = {
        'page_obj': page_obj,
        'total_phones': total_phones,
        'search_query': search_query,
    }
    return render(request, 'registration/phone_history.html', context)


def export_phones_to_excel(request):
    """
    Export تمام شماره‌های ثبت شده به فایل اکسل
    """
    # دریافت تمام شماره‌ها
    phones = PhoneRequest.objects.all().order_by('-created_at')
    
    # ایجاد DataFrame
    data = {
        'ردیف': range(1, len(phones) + 1),
        'شماره تلفن': [str(phone.phone) for phone in phones],
        'تاریخ ثبت': [phone.created_at.strftime('%Y/%m/%d') for phone in phones],
        'ساعت ثبت': [phone.created_at.strftime('%H:%M:%S') for phone in phones],
    }
    
    df = pd.DataFrame(data)
    
    # ایجاد response با فرمت اکسل
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # نام فایل با تاریخ و زمان
    filename = f'phone_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # نوشتن DataFrame به response
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='تاریخچه شماره‌ها')
    
    return response


def dashboard_view(request):
    """
    داشبورد نمایش اطلاعات و آمار
    """
    # آمار کلی PhoneRequest
    total_phones = PhoneRequest.objects.count()
    
    # آمار امروز
    today = timezone.now().date()
    today_phones = PhoneRequest.objects.filter(created_at__date=today).count()
    
    # آمار این هفته
    week_ago = timezone.now() - timedelta(days=7)
    week_phones = PhoneRequest.objects.filter(created_at__gte=week_ago).count()
    
    # آمار این ماه
    month_ago = timezone.now() - timedelta(days=30)
    month_phones = PhoneRequest.objects.filter(created_at__gte=month_ago).count()
    
    # آخرین شماره‌های ثبت شده
    recent_phones = PhoneRequest.objects.all().order_by('-created_at')[:10]
    
    # آمار روزانه (7 روز اخیر)
    daily_stats = PhoneRequest.objects.filter(
        created_at__gte=week_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # آمار ماهانه (6 ماه اخیر)
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_stats = PhoneRequest.objects.filter(
        created_at__gte=six_months_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # آمار UserData
    total_users = UserData.objects.count()
    recent_users = UserData.objects.all().order_by('-created_at')[:5]
    
    # آماده‌سازی داده‌ها برای نمودار
    daily_labels = [stat['date'].strftime('%Y/%m/%d') for stat in daily_stats]
    daily_data = [stat['count'] for stat in daily_stats]
    
    monthly_labels = [stat['month'].strftime('%Y/%m') for stat in monthly_stats]
    monthly_data = [stat['count'] for stat in monthly_stats]
    
    context = {
        'total_phones': total_phones,
        'today_phones': today_phones,
        'week_phones': week_phones,
        'month_phones': month_phones,
        'recent_phones': recent_phones,
        'total_users': total_users,
        'recent_users': recent_users,
        'daily_labels': daily_labels,
        'daily_data': daily_data,
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
    }
    
    return render(request, 'registration/dashboard.html', context)


# app/views.py
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import SherlockSearch
from .sherlock_utils import run_sherlock_search  # ✅ import

@login_required
def sherlock_search(request):
    """
    صفحه جستجوی نام کاربری
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        
        if not username:
            messages.error(request, 'لطفاً نام کاربری را وارد کنید')
            return redirect('sherlock_search')
        
        # ذخیره در دیتابیس
        search_record = SherlockSearch.objects.create(
            username=username,
            status='pending'
        )
        
        # اجرای Sherlock
        result = run_sherlock_search(username)  # ✅ استفاده از utils
        
        # ذخیره نتایج
        if result['success']:
            search_record.status = 'completed'
            search_record.results = result['data']
            search_record.total_found = result['found_count']
            search_record.save()
            messages.success(request, f'✅ جستجو تکمیل شد! {result["found_count"]} پروفایل پیدا شد')
        else:
            search_record.status = 'failed'
            search_record.results = result  # ذخیره کل دیکشنری خطا
            search_record.save()
            messages.error(request, f'❌ خطا: {result.get('error', 'خطای نامشخص')}')
        
            return redirect('app:sherlock_result', pk=search_record.pk)
    
    # نمایش فرم
    recent_searches = SherlockSearch.objects.all()[:10]
    return render(request, 'registration/sherlock_search.html', {
        'recent_searches': recent_searches
    })


@login_required
def sherlock_result(request, pk):
    """
    نمایش نتایج جستجو
    """
    search_record = get_object_or_404(SherlockSearch, pk=pk)

    # استخراج پروفایل‌های پیدا شده
    found_profiles = {}
    error_details = None

    # دیباگ: نمایش مقدار دقیق نتایج
    print("\n================= DEBUG SHERLOCK RESULT =================")
    print(f"search_record.results: {json.dumps(search_record.results, ensure_ascii=False, indent=2) if search_record.results else search_record.results}")

    if search_record.results:
        if isinstance(search_record.results, dict):
            if 'error' in search_record.results:
                error_details = search_record.results
            else:
                for site, data in search_record.results.items():
                    if isinstance(data, dict) and data.get('url_user'):
                        found_profiles[site] = data
        elif isinstance(search_record.results, str):
            # خروجی متنی: استخراج لینک پروفایل‌ها
            lines = search_record.results.splitlines()
            for line in lines:
                if line.strip().startswith('[+]'):
                    try:
                        site_part, url = line.split(':', 1)
                        site = site_part.replace('[+]', '').strip()
                        url = url.strip()
                        found_profiles[site] = {'url_user': url}
                    except Exception:
                        continue
    print(f"found_profiles: {json.dumps(found_profiles, ensure_ascii=False, indent=2)}")
    print("========================================================\n")

    return render(request, 'registration/sherlock_result.html', {
        'search': search_record,
        'found_profiles': found_profiles,
        'error_details': error_details
    })
    
@login_required
@require_http_methods(["POST"])
def sherlock_search_delete(request, pk):
    """
    حذف یک جستجوی Sherlock
    """
    search_record = get_object_or_404(SherlockSearch, pk=pk)
    username = search_record.username
    
    try:
        search_record.delete()
        messages.success(request, f'جستجوی "{username}" با موفقیت حذف شد')
    except Exception as e:
        messages.error(request, f'خطا در حذف جستجو: {str(e)}')
    
    return redirect('app:sherlock_search')