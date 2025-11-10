import subprocess
import json
from pathlib import Path
from django.conf import settings

def run_sherlock_search(username):
    """
    اجرای Sherlock و بازگشت نتایج
    """
    # مسیر sherlock_project داخل پوشه sherlock
    sherlock_dir = Path(settings.BASE_DIR) / 'sherlock'
    sherlock_script = sherlock_dir / 'sherlock_project' / 'sherlock.py'
    
    # دیگر نیازی به فایل خروجی نیست، فقط خروجی stdout را می‌خوانیم
    
    try:
        # بررسی وجود فایل sherlock
        if not sherlock_script.exists():
            return {
                'success': False,
                'error': f'فایل sherlock پیدا نشد در مسیر: {sherlock_script}'
            }
        
        # اجرای Sherlock فقط با --print-found
        result = subprocess.run(
            [
                'python3',
                str(sherlock_script),
                username,
                '--timeout', '10',
                '--print-found'
            ],
            capture_output=True,
            text=True,
            cwd=str(sherlock_dir),
            timeout=120
        )

        # استخراج لینک‌های پروفایل از stdout
        found_profiles = {}
        lines = result.stdout.splitlines()
        for line in lines:
            # مثال: [+] DeviantArt: https://www.deviantart.com/behnam_am_m
            if line.strip().startswith('[+]'):
                try:
                    site_part, url = line.split(':', 1)
                    site = site_part.replace('[+]', '').strip()
                    url = url.strip()
                    found_profiles[site] = {'url_user': url}
                except Exception:
                    continue

        return {
            'success': True if found_profiles else False,
            'data': result.stdout,
            'found_count': len(found_profiles),
            'found_profiles': found_profiles,
            'output': result.stdout,
            'errors': result.stderr
        }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'زمان جستجو به پایان رسید (بیش از 2 دقیقه)'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'خطا: {str(e)}'
        }