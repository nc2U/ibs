from django.urls import path

from .views import CompanyRegisterView, CompanyCV

app_name = 'company'

urlpatterns = [
    path('', CompanyRegisterView.as_view(), name='index'),
    path('create/', CompanyCV.as_view(), name='create'),
]
