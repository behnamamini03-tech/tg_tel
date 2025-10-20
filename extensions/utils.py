from . import jalali
import datetime

def jalali_converter(time):   
    from django.utils import timezone
    jmonths = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    # اگر datetime است و aware است، به منطقه زمانی محلی تبدیل کن
    if isinstance(time, datetime.datetime):
        if timezone.is_aware(time):
            time = timezone.localtime(time)
    time_to_str = '{},{},{}'.format(time.year, time.month, time.day)
    time_to_tuple = jalali.Gregorian(time_to_str).persian_tuple()
    time_to_list = list(time_to_tuple)
    for index, month in enumerate(jmonths):
        if time_to_list[1] == index + 1:
            time_to_list[1] = month
            break
    if isinstance(time, datetime.datetime):
        output = "{},{},{}, ساعت {}:{}".format(time_to_list[2], time_to_list[1], time_to_list[0], time.hour, time.minute)
    else:
        output = "{},{},{}".format(time_to_list[2], time_to_list[1], time_to_list[0])
    return output