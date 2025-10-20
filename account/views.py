from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from app.models import PhoneRequest, UserData

@login_required
def home(request):
    return render(request, 'registration/home.html')

# class PhoneRequestList(LoginRequiredMixin, ListView):
#     model = PhoneRequest
#     template_name = 'account/phone_request_list.html'
#     context_object_name = 'phone_requests'

#     def get_queryset(self):
#         return PhoneRequest.objects.all()
    

# class UserDataList(LoginRequiredMixin, ListView):
#     model = UserData
#     template_name = 'account/user_data_list.html'
#     context_object_name = 'user_data_list'

#     def get_queryset(self):
#         return UserData.objects.all()