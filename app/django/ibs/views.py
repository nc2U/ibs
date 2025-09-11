from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import generic
from django.views.generic import TemplateView

from accounts.models import User
from company.models import Company
from ibs.models import ProjectAccountD3
from project.models import Project

# --------------------------------------------------------

TODAY = date.today()


def install_check(request):
    # Check if basic installation data exists (more comprehensive check)
    has_superuser = User.objects.filter(is_superuser=True).exists()
    has_company = Company.objects.exists()
    has_project = Project.objects.exists()
    is_d3 = ProjectAccountD3.objects.exists()

    # Consider installation complete if we have basic entities even without D3 data
    installation_complete = has_superuser and has_company and (has_project or is_d3)

    if installation_complete:
        return render(request, 'base-vue.html')
    else:
        return redirect('/install/')


class Dashboard(LoginRequiredMixin, TemplateView):
    template_name = 'ibs/main/1_1_dashboard.html'


def menu2_1(request):
    return render(request, 'ibs/main/2_1_schedule.html')


class CustomHandler404(generic.View):
    @staticmethod
    def get(request):
        context = {}
        return render(request, "errors/404.html", context)


def handler500(request):
    context = {}
    response = render(request, "errors/500.html", context=context)
    response.status_code = 500
    return response
