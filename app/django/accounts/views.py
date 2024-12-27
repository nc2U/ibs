import subprocess
from django import forms
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from .models import User
from company.models import Company
from project.models import Project
from ibs.models import ProjectAccountD3

from .forms import UserCreationForm


class UserCreateView(CreateView):
    template_name = 'registration/register.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('register_done')


class UserCreateDoneTV(TemplateView):
    template_name = 'registration/register_done.html'


def install_check_step(request):
    is_superuser = User.objects.filter(is_superuser=True).exists()
    is_company = Company.objects.exists()
    is_project = Project.objects.exists()

    is_d3 = ProjectAccountD3.objects.exists()
    if is_d3:
        return redirect('/')

    if not is_superuser:
        return redirect('/install/create/superuser/')
    elif not is_company:
        return redirect('/install/create/company/')
    elif not is_project:
        return redirect('/install/create/project/')
    else:
        return redirect('/')


def create_superuser(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords don't match!")
        else:
            User.objects.create_superuser(username=username,
                                          email=email,
                                          password=password)
        return redirect('/install/create/company/')
    else:

        is_d3 = ProjectAccountD3.objects.exists()
        if is_d3:
            return redirect('/')
        is_superuser = User.objects.filter(is_superuser=True).exists()
        if is_superuser:
            return redirect('/install/create/company/')
        else:
            return render(request, 'install/create_superuser.html')


def create_company(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        tax_number = request.POST.get('tax_number')
        ceo = request.POST.get('ceo')
        org_number = request.POST.get('org_number')
        Company.objects.create(name=name,
                               tax_number=tax_number,
                               ceo=ceo,
                               org_number=org_number)
        return redirect('/install/create/project/')
    else:
        is_d3 = ProjectAccountD3.objects.exists()
        if is_d3:
            return redirect('/')
        is_superuser = User.objects.filter(is_superuser=True).exists()
        is_company = Company.objects.all().exists()
        if not is_superuser:
            return redirect('/install/create/superuser/')
        elif not is_company:
            return render(request, 'install/create_company.html')
        else:
            return redirect('/install/create/project/')


def load_seed_data():
    cmd = 'python manage.py loaddata ibs/fixtures/seeds-data.json'
    subprocess.call(cmd, shell=True)


def create_project(request):
    d3 = ProjectAccountD3.objects.exists()
    if request.method == 'POST':
        company = request.POST.get('company')
        name = request.POST.get('name')
        kind = request.POST.get('kind')
        start_year = request.POST.get('start_year')
        local_zipcode = request.POST.get('local_zipcode')
        local_address1 = request.POST.get('local_address1')
        local_address2 = request.POST.get('local_address2')
        local_address3 = request.POST.get('local_address3')
        area_usage = request.POST.get('area_usage')
        build_size = request.POST.get('build_size')
        Project.objects.create(company_id=company,
                               name=name,
                               kind=kind,
                               start_year=start_year,
                               local_zipcode=local_zipcode,
                               local_address1=local_address1,
                               local_address2=local_address2,
                               local_address3=local_address3,
                               area_usage=area_usage,
                               build_size=build_size)

        if not d3:
            load_seed_data()
        return redirect('/')
    else:
        if d3:
            return redirect('/')
        is_company = Company.objects.all().exists()
        if not is_company:
            return redirect('/install/create/company/')
        else:
            companies = Company.objects.all()
            return render(request, 'install/create_project.html', {'companies': companies})


def pass_create_project(request):
    d3 = ProjectAccountD3.objects.exists()
    if not d3:
        load_seed_data()
    return redirect('/')
