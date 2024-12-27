from datetime import date

from django.http import HttpResponse
from django.views import generic
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
# --------------------------------------------------------
from ibs.models import ProjectAccountD3

TODAY = date.today()


def install_check(request):
    is_d3 = ProjectAccountD3.objects.exists()

    if is_d3:
        return render(request, 'base-vue.html')
    else:
        return redirect('/install/')


class Dashboard(LoginRequiredMixin, TemplateView):
    template_name = 'rebs/main/1_1_dashboard.html'


def menu2_1(request):
    return render(request, 'rebs/main/2_1_schedule.html')


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
