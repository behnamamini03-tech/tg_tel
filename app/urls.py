from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.phone_request_view, name='phone_request'),
    path('history/', views.phone_history_view, name='phone_history'),
    path('history/export/', views.export_phones_to_excel, name='export_phones'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]

 