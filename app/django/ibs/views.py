from django.shortcuts import render, redirect
from django.views import generic

from accounts.models import User
from company.models import Company
from ibs.models import ProjectAccountD3
from project.models import Project


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


class CustomHandler404(generic.View):
    def dispatch(self, request, *args, **kwargs):
        context = {}
        return render(request, "errors/404.html", context, status=404)


def handler500(request):
    context = {}
    response = render(request, "errors/500.html", context=context)
    response.status_code = 500
    return response
