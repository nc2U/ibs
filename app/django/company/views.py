from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, FormView
from django.views.generic.list import ListView

from .forms import CompanyForm
from .models import Company


class CompanyRegisterView(LoginRequiredMixin, ListView, FormView):
    model = Company
    form_class = CompanyForm

    def get_form(self, form_class=None):
        initial = {}
        company_id = self.request.GET.get('id')
        if company_id:
            company = Company.objects.filter(pk=company_id).first()
            if company:
                initial = {
                    'name': company.name,
                    'tax_number': company.tax_number,
                    'ceo': company.ceo,
                    'org_number': company.org_number,
                    'business_cond': company.business_cond,
                    'business_even': company.business_even,
                    'es_date': company.es_date,
                    'op_date': company.op_date,
                    'zipcode': company.zipcode,
                    'address1': company.address1,
                    'address2': company.address2,
                    'address3': company.address3,
                }
        return self.form_class(initial=initial)

    def post(self, request, *args, **kwargs):
        company_id = request.GET.get('id')
        company = Company.objects.filter(pk=company_id).first() if company_id else None
        form = self.form_class(request.POST, instance=company)

        if form.is_valid():
            form.save()
            return redirect(reverse_lazy('ibs:company:index'))
        return render(request, 'company/company_list.html', {'form': form})


class CompanyCV(LoginRequiredMixin, CreateView):
    model = Company
    fields = [
        'name', 'tax_number',
        'ceo', 'org_number',
        'business_cond', 'business_even',
        'es_date', 'op_date',
        'zipcode', 'address1', 'address2', 'address3'
    ]
    success_url = reverse_lazy('ibs:company:index')
