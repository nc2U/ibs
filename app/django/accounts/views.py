import datetime
import os
import subprocess

from django import forms
from django.core.management import call_command
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView

from cash.models import CompanyCashBookCalculation, ProjectCashBookCalculation
from company.models import Company
from ibs.models import ProjectAccountD3
from project.models import Project
from work.models import Role, Tracker, CodeActivity
from work.models.project import IssueProject, Module
from .forms import UserCreationForm
from .models import User


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
        company = Company.objects.create(name=name,
                                         tax_number=tax_number,
                                         ceo=ceo,
                                         org_number=org_number)
        company.save()
        CompanyCashBookCalculation.objects.create(company=company, calculated=datetime.date.today(), creator_id=1)
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
    try:
        # Use Django's call_command instead of subprocess for better reliability
        call_command('loaddata', 'ibs/fixtures/seeds-data.json')
    except Exception as e:
        # Fallback to subprocess if needed
        cmd = 'python manage.py loaddata ibs/fixtures/seeds-data.json'
        subprocess.call(cmd, shell=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_project(request):
    d3 = ProjectAccountD3.objects.exists()
    if not d3:
        load_seed_data()

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

        kind_name = {'1': '공동주택(아파트)',
                     '2': '공동주택(타운하우스)',
                     '3': '주상복합(아파트)',
                     '4': '주상복합(오피스텔)',
                     '5': '근린생활시설',
                     '6': '생활형숙박시설',
                     '7': '지식산업센터',
                     '8': '기타'}[kind]

        issue_project = IssueProject.objects.create(company_id=company,
                                                    sort='2',
                                                    name=name,
                                                    slug='proj1',
                                                    description=f'{name} {kind_name} 신축사업',
                                                    creator_id=1)
        # Add roles if they exist

        existing_roles = list(Role.objects.filter(pk__in=[6, 7, 8]).values_list('pk', flat=True))
        if existing_roles:
            issue_project.allowed_roles.add(*existing_roles)

        existing_trackers = list(Tracker.objects.filter(pk__in=[4, 5, 6, 7]).values_list('pk', flat=True))
        if existing_trackers:
            issue_project.trackers.add(*existing_trackers)

        existing_activities = list(CodeActivity.objects.filter(pk__in=[3, 4, 5, 6, 7, 8]).values_list('pk', flat=True))
        if existing_activities:
            issue_project.activities.add(*existing_activities)
        issue_project.save()

        Module(project=issue_project, issue=True, time=True, news=True,
               document=True, file=True, wiki=True, repository=False,
               forum=True, calendar=True, gantt=True).save()

        project = Project.objects.create(issue_project=issue_project,
                                         name=name,
                                         kind=kind,
                                         start_year=start_year,
                                         local_zipcode=local_zipcode,
                                         local_address1=local_address1,
                                         local_address2=local_address2,
                                         local_address3=local_address3,
                                         area_usage=area_usage,
                                         build_size=build_size)
        project.save()
        ProjectCashBookCalculation.objects.create(project=project, calculated=datetime.date.today(), creator_id=1)
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
