from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin

from django.views.generic import TemplateView, ListView, CreateView, UpdateView, FormView

from datetime import datetime, timedelta
from django.db.models import Q, Sum

from .forms import (CashSearchForm, ProjectCashSearchForm, PaymentSearchForm, PaymentForm,
                    CashBookFormSet, ProjectCashBookFormSet)

from .models import CompanyBankAccount, ProjectBankAccount, CashBook, ProjectCashBook
from payment.models import SalesPriceByGT, InstallmentPaymentOrder, DownPayment
from ibs.models import (AccountSort, AccountSubD1, AccountSubD2, AccountSubD3,
                        ProjectAccountD2, ProjectAccountD3)
from company.models import Company
from project.models import Project, ProjectOutBudget
from items.models import UnitType, KeyUnit
from contract.models import OrderGroup, Contract

TODAY = datetime.today().strftime('%Y-%m-%d')


class DaylyCashReport(LoginRequiredMixin, TemplateView):
    template_name = 'cash/cashbook_report.html'

    def get_context_data(self, **kwargs):
        context = super(DaylyCashReport, self).get_context_data(**kwargs)
        context['bank_accounts'] = CompanyBankAccount.objects.all()
        context['confirm_date'] = self.request.GET.get('confirm_date') if self.request.GET.get(
            'confirm_date') else TODAY
        yesterday = datetime.strptime(context['confirm_date'], '%Y-%m-%d') - timedelta(days=1)
        context['yesterday'] = yesterday.strftime('%Y-%m-%d')

        ba_1day_ago_total = []  # 전일잔고
        ba_to_inc = []  # 금일 입금
        ba_to_out = []  # 금일 출금
        ba_totay_balance = []  # 금일 잔고

        ba_1day_ago_total_sum = 0
        ba_to_inc_sum = 0
        ba_to_out_sum = 0
        ba_totay_balance_sum = 0

        for i, ba in enumerate(context['bank_accounts']):
            # 어제까지의 토탈 income, outlay
            ba_yi = CashBook.objects.filter(
                bank_account=ba, deal_date__lte=context['yesterday']).aggregate(Sum('income'))
            ba_uy_inc = ba_yi['income__sum'] if ba_yi['income__sum'] else 0  # 입금 내역이 없으면 0

            ba_yo = CashBook.objects.filter(
                bank_account=ba, deal_date__lte=context['yesterday']).aggregate(Sum('outlay'))
            ba_uy_out = ba_yo['outlay__sum'] if ba_yo['outlay__sum'] else 0  # 출금 내역이 없으면 0

            # 기준일자 토탈 income, outlay
            ba_ti = CashBook.objects.filter(
                bank_account=ba,
                deal_date__exact=context['confirm_date']).aggregate(Sum('income'))

            ba_to = CashBook.objects.filter(
                bank_account=ba,
                deal_date__exact=context['confirm_date']).aggregate(Sum('outlay'))

            ba_1day_ago_total.append(ba_uy_inc - ba_uy_out)
            ba_to_inc.append(ba_ti['income__sum'] if ba_ti['income__sum'] else 0)
            ba_to_out.append(ba_to['outlay__sum'] if ba_to['outlay__sum'] else 0)
            ba_totay_balance.append(ba_1day_ago_total[i] + ba_to_inc[i] - ba_to_out[i])

            ba_1day_ago_total_sum += ba_1day_ago_total[i]
            ba_to_inc_sum += ba_to_inc[i]
            ba_to_out_sum += ba_to_out[i]
            ba_totay_balance_sum += ba_totay_balance[i]

        ba_1day_ago_total = list(reversed(ba_1day_ago_total))  # 전일잔고
        ba_to_inc = list(reversed(ba_to_inc))  # 금일 입금
        ba_to_out = list(reversed(ba_to_out))  # 금일 출금
        ba_totay_balance = list(reversed(ba_totay_balance))  # 금일 잔고

        def new_list(x):
            x = x if x != 0 else "-"
            return x

        context['ba_1day_ago_total'] = list(map(new_list, ba_1day_ago_total))  # 전일잔고
        context['ba_to_inc'] = list(map(new_list, ba_to_inc))  # 금일 입금
        context['ba_to_out'] = list(map(new_list, ba_to_out))  # 금일 출금
        context['ba_totay_balance'] = list(map(new_list, ba_totay_balance))  # 금일 잔고

        context['ba_1day_ago_total_sum'] = ba_1day_ago_total_sum if ba_1day_ago_total_sum != 0 else "-"
        context['ba_to_inc_sum'] = ba_to_inc_sum if ba_to_inc_sum != 0 else "-"
        context['ba_to_out_sum'] = ba_to_out_sum if ba_to_out_sum != 0 else "-"
        context['ba_totay_balance_sum'] = ba_totay_balance_sum if ba_totay_balance_sum != 0 else "-"

        # 당일 입출금 데이터
        cashbook_data = CashBook.objects.all().order_by('deal_date', 'created', 'id')
        context['day_inc_list'] = CashBook.objects.filter(income__isnull=False,
                                                          deal_date__exact=context['confirm_date'])
        context['day_out_list'] = cashbook_data.filter(outlay__isnull=False,
                                                       deal_date__exact=context['confirm_date'])

        context['day_inc_sum'] = cashbook_data.filter(income__isnull=False,
                                                      deal_date__exact=context['confirm_date']).aggregate(
            Sum('income'))
        context['day_out_sum'] = cashbook_data.filter(outlay__isnull=False,
                                                      deal_date__exact=context['confirm_date']).aggregate(
            Sum('outlay'))
        return context


class CashInoutLV(LoginRequiredMixin, ListView, FormView):
    model = CashBook
    form_class = CashSearchForm
    paginate_by = 15

    def get_queryset(self):
        company = Company.objects.first()
        results = CashBook.objects.filter(company=company).order_by('-deal_date', '-id')

        if self.request.GET.get('s_date'):
            results = results.filter(deal_date__gte=self.request.GET.get('s_date'))

        if self.request.GET.get('e_date'):
            results = results.filter(deal_date__lte=self.request.GET.get('e_date'))

        if self.request.GET.get('sort'):
            results = results.filter(sort__id=self.request.GET.get('sort'))

        if self.request.GET.get('account_d1'):
            results = results.filter(account_d1__id=self.request.GET.get('account_d1'))

        if self.request.GET.get('bank_account'):
            results = results.filter(bank_account__id=self.request.GET.get('bank_account'))

        if self.request.GET.get('search_word'):
            results = results.filter(
                Q(account_d3__name__icontains=self.request.GET.get('search_word', '')) |
                Q(content__icontains=self.request.GET.get('search_word', '')) |
                Q(trader__icontains=self.request.GET.get('search_word', ''))
            )
        return results

    def get_context_data(self, **kwargs):
        context = super(CashInoutLV, self).get_context_data(**kwargs)
        context['d1_account'] = d1_account = AccountSubD1.objects.exclude(name='대체')
        d2_account = []
        d3_account = []
        for d1 in d1_account:
            d2_acc = AccountSubD2.objects.filter(d1=d1)
            d2_account.append(d2_acc)
            for d2 in d2_acc:
                d3_acc = AccountSubD3.objects.filter(d2=d2)
                d3_account.append(d3_acc)

        context['d2_account'] = list(reversed(d2_account))
        context['d3_account'] = list(reversed(d3_account))
        return context


class CashInoutCV(LoginRequiredMixin, CreateView):
    model = CashBook
    fields = ('deal_date',)
    success_url = reverse_lazy('ibs:cash-inout:index')

    def get_context_data(self, **kwargs):
        context = super(CashInoutCV, self).get_context_data(**kwargs)
        context['company'] = Company.objects.first()
        context['bank_account'] = CompanyBankAccount.objects.filter(company=context['company'])
        context['account_1'] = AccountSubD3.objects.filter(d2__d1_id=1)
        context['account_2'] = AccountSubD3.objects.filter(d2__d1_id=2)
        context['account_3'] = AccountSubD3.objects.filter(d2__d1_id=3)
        context['account_4'] = AccountSubD3.objects.filter(d2__d1_id=4)
        context['account_5'] = AccountSubD3.objects.filter(d2__d1_id=5)
        context['formset'] = CashBookFormSet(queryset=CashBook.objects.none())
        context['d1_account'] = d1_account = AccountSubD1.objects.exclude(name='대체')
        d2_account = []
        d3_account = []
        for d1 in d1_account:
            d2_acc = AccountSubD2.objects.filter(d1=d1)
            d2_account.append(d2_acc)
            for d2 in d2_acc:
                d3_acc = AccountSubD3.objects.filter(d2=d2)
                d3_account.append(d3_acc)

        context['d2_account'] = list(reversed(d2_account))
        context['d3_account'] = list(reversed(d3_account))
        return context

    def form_valid(self, form):
        formset = CashBookFormSet(self.request.POST)
        if formset.is_valid():
            for form in formset:
                instance = form.save(commit=False)
                instance.company = Company.objects.first()
                instance.deal_date = self.request.POST.get('deal_date')
                instance.user = self.request.user
                instance.save()
        return super(CashInoutCV, self).form_valid(form)


class CashInoutUV(LoginRequiredMixin, UpdateView):
    model = CashBook


def CashInoutDV(request, *args, **kwargs):
    cash_inout = CashBook.objects.get(pk=kwargs['pk'])
    cash_inout.delete()
    return redirect(reverse_lazy('ibs:cash-inout:index'))


class ProjectCashReport(LoginRequiredMixin, TemplateView):
    template_name = 'cash/projectcashbook_report.html'

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_context_data(self, **kwargs):
        context = super(ProjectCashReport, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['bank_accounts'] = ProjectBankAccount.objects.filter(project=self.get_project(), directpay=False)
        context['confirm_date'] = self.request.GET.get('confirm_date') if self.request.GET.get(
            'confirm_date') else TODAY
        yesterday = datetime.strptime(context['confirm_date'], '%Y-%m-%d') - timedelta(days=1)
        context['yesterday'] = yesterday.strftime('%Y-%m-%d')

        ba_1day_ago_total = []  # 전일잔고
        ba_to_inc = []  # 금일 입금
        ba_to_out = []  # 금일 출금
        ba_totay_balance = []  # 금일 잔고

        ba_1day_ago_total_sum = 0
        ba_to_inc_sum = 0
        ba_to_out_sum = 0
        ba_totay_balance_sum = 0

        for i, ba in enumerate(context['bank_accounts']):
            # 어제까지의 토탈 income, outlay
            ba_yi = ProjectCashBook.objects.filter(
                project=self.get_project(),
                is_separate=False,
                bank_account=ba, deal_date__lte=context['yesterday']).aggregate(Sum('income'))
            ba_uy_inc = ba_yi['income__sum'] if ba_yi['income__sum'] else 0  # 입금 내역이 없으면 0

            ba_yo = ProjectCashBook.objects.filter(
                project=self.get_project(),
                is_separate=False,
                bank_account=ba, deal_date__lte=context['yesterday']).aggregate(Sum('outlay'))
            ba_uy_out = ba_yo['outlay__sum'] if ba_yo['outlay__sum'] else 0  # 출금 내역이 없으면 0

            # 기준일자 토탈 income, outlay
            ba_ti = ProjectCashBook.objects.filter(
                project=self.get_project(),
                is_separate=False,
                bank_account=ba,
                deal_date__exact=context['confirm_date']).aggregate(Sum('income'))

            ba_to = ProjectCashBook.objects.filter(
                project=self.get_project(),
                is_separate=False,
                bank_account=ba,
                deal_date__exact=context['confirm_date']).aggregate(Sum('outlay'))

            ba_1day_ago_total.append(ba_uy_inc - ba_uy_out)
            ba_to_inc.append(ba_ti['income__sum'] if ba_ti['income__sum'] else 0)
            ba_to_out.append(ba_to['outlay__sum'] if ba_to['outlay__sum'] else 0)
            ba_totay_balance.append(ba_1day_ago_total[i] + ba_to_inc[i] - ba_to_out[i])

            ba_1day_ago_total_sum += ba_1day_ago_total[i]
            ba_to_inc_sum += ba_to_inc[i]
            ba_to_out_sum += ba_to_out[i]
            ba_totay_balance_sum += ba_totay_balance[i]

        ba_1day_ago_total = list(reversed(ba_1day_ago_total))  # 전일잔고
        ba_to_inc = list(reversed(ba_to_inc))  # 금일 입금
        ba_to_out = list(reversed(ba_to_out))  # 금일 출금
        ba_totay_balance = list(reversed(ba_totay_balance))  # 금일 잔고

        def new_list(x):
            x = x if x != 0 else "-"
            return x

        context['ba_1day_ago_total'] = list(map(new_list, ba_1day_ago_total))  # 전일잔고
        context['ba_to_inc'] = list(map(new_list, ba_to_inc))  # 금일 입금
        context['ba_to_out'] = list(map(new_list, ba_to_out))  # 금일 출금
        context['ba_totay_balance'] = list(map(new_list, ba_totay_balance))  # 금일 잔고

        context['ba_1day_ago_total_sum'] = ba_1day_ago_total_sum if ba_1day_ago_total_sum != 0 else "-"
        context['ba_to_inc_sum'] = ba_to_inc_sum if ba_to_inc_sum != 0 else "-"
        context['ba_to_out_sum'] = ba_to_out_sum if ba_to_out_sum != 0 else "-"
        context['ba_totay_balance_sum'] = ba_totay_balance_sum if ba_totay_balance_sum != 0 else "-"

        # 당일 입출금 데이터
        project_cashbook = ProjectCashBook.objects.all().order_by('deal_date', 'created', 'id')
        context['day_inc_list'] = project_cashbook.filter(project=self.get_project(), is_separate=False,
                                                          income__isnull=False,
                                                          deal_date__exact=context['confirm_date'])
        context['day_out_list'] = project_cashbook.filter(project=self.get_project(), is_separate=False,
                                                          outlay__isnull=False,
                                                          deal_date__exact=context['confirm_date'])
        context['day_inc_sum'] = project_cashbook.filter(project=self.get_project(), is_separate=False,
                                                         income__isnull=False,
                                                         deal_date__exact=context['confirm_date']).aggregate(
            Sum('income'))
        context['day_out_sum'] = project_cashbook.filter(project=self.get_project(), is_separate=False,
                                                         outlay__isnull=False,
                                                         deal_date__exact=context['confirm_date']).aggregate(
            Sum('outlay'))
        # 예산관련 데이터(수입)
        context['order_group'] = OrderGroup.objects.filter(project=self.get_project())
        context['unit_type'] = UnitType.objects.filter(project=self.get_project())

        # 예산관련 데이터(집행)
        context['project_budgets'] = bg = ProjectOutBudget.objects.filter(project=self.get_project(),
                                                                          account_d2__d1__accountsort=2,
                                                                          account_d2__d1__code__startswith="3")
        context['rsp1'] = bg.filter(account_d2__code__range=('322', '326')).count()  # 간접공사비
        context['rsp2'] = bg.filter(account_d2__code__range=('327', '329')).count()  # 설계용역비
        context['rsp22'] = 6 + context['rsp1']
        context['rsp3'] = bg.filter(account_d2__code__range=('331', '339')).count()  # 판매비
        context['rsp4'] = bg.filter(account_d2__code__range=('341', '349')).count()  # 일반관리비
        context['rsp44'] = context['rsp22'] + context['rsp2'] + context['rsp3']
        context['rsp5'] = bg.filter(account_d2__code__range=('351', '359')).count()  # 제세공과금
        context['rsp55'] = context['rsp44'] + context['rsp4']

        # 예산항목별 출금 집계
        month_budget = []
        pcash_list_by_budget = []

        for budget in context['project_budgets']:
            # 예산항목별 출금액
            pcash_budget_data = ProjectCashBook.objects.filter(project=self.get_project(),
                                                               is_separate=False,
                                                               project_account_d3=budget.account_d3,
                                                               deal_date__lte=context['confirm_date'])
            pcash_budget_month = pcash_budget_data.filter(deal_date__gte=context['confirm_date'][:8] + '01').aggregate(
                Sum('outlay'))
            pcash_budget_total = pcash_budget_data.aggregate(Sum('outlay'))
            # 상기 출금액 배열로 집계
            month_budget.append(pcash_budget_month['outlay__sum'] if pcash_budget_month['outlay__sum'] else 0)
            pcash_list_by_budget.append(pcash_budget_total['outlay__sum'] if pcash_budget_total['outlay__sum'] else 0)

        month_budget = list(reversed(month_budget))
        context['month_budget'] = month_budget
        pcash_list_by_budget = list(reversed(pcash_list_by_budget))
        context['pcash_list_by_budget'] = pcash_list_by_budget

        # 예산 총액
        context['project_budgets_sum'] = context['project_budgets'].aggregate(Sum('budget'))
        context['month_budget_sum'] = sum(month_budget)
        context['pcash_budget_sum'] = sum(pcash_list_by_budget)
        return context


class ProjectCashInoutLV(LoginRequiredMixin, ListView, FormView):
    model = ProjectCashBook
    form_class = ProjectCashSearchForm
    paginate_by = 15

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_form_kwargs(self):
        kwargs = super(ProjectCashInoutLV, self).get_form_kwargs()
        kwargs['project'] = self.get_project()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(ProjectCashInoutLV, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['pa_d2'] = ProjectAccountD2.objects.all() \
            if self.request.GET.get('sort') == '' \
            else ProjectAccountD2.objects.filter(
            accountsort=self.request.GET.get('sort'))
        context['pa_d2_inc'] = ProjectAccountD2.objects.filter(accountsort=1)
        context['pa_d2_out'] = ProjectAccountD2.objects.filter(accountsort=2)
        context['pa_d2_trans'] = ProjectAccountD2.objects.filter(accountsort=3)
        pa_d3 = ProjectAccountD3.objects.all()
        if self.request.GET.get('d2'):
            pa_d3 = pa_d3.filter(d1_id__exact=int(self.request.GET.get('d2')))
        context['pa_d3'] = pa_d3
        context['bank_account'] = ProjectBankAccount.objects.filter(project=self.get_project())
        context['auth_date'] = datetime.today().date() - timedelta(days=10)
        return context

    def get_queryset(self):
        project = self.get_project()
        results = ProjectCashBook.objects.filter(project=project).order_by('-deal_date', '-id')

        if self.request.GET.get('sdate'):
            results = results.filter(deal_date__gte=self.request.GET.get('sdate'))

        if self.request.GET.get('edate'):
            results = results.filter(deal_date__lte=self.request.GET.get('edate'))

        if self.request.GET.get('sort'):
            results = results.filter(sort=self.request.GET.get('sort'))

        if self.request.GET.get('d2'):
            results = results.filter(project_account_d2__id=self.request.GET.get('d2'))

        if self.request.GET.get('d3'):
            results = results.filter(project_account_d3__id=self.request.GET.get('d3'))

        if self.request.GET.get('bank_acc'):
            results = results.filter(bank_account__id=self.request.GET.get('bank_acc'))

        if self.request.GET.get('q'):
            results = results.filter(
                Q(content__icontains=self.request.GET.get('q')) |
                Q(trader__icontains=self.request.GET.get('q'))
            )
        return results


class ProjectCashInoutCV(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    model = ProjectCashBook
    success_message = '해당 거래가 등록되었습니다.'
    fields = ('deal_date',)

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_success_url(self):
        project_query = '?project=' + self.request.POST.get('project')
        return reverse_lazy('ibs:cash-inout:project-index') + project_query

    def get_context_data(self, **kwargs):
        context = super(ProjectCashInoutCV, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['pa_d2_inc'] = ProjectAccountD2.objects.filter(accountsort=1)
        context['pa_d2_out'] = ProjectAccountD2.objects.filter(accountsort=2)
        context['pa_d2_trans'] = ProjectAccountD2.objects.filter(accountsort=3)
        context['pa_d3_inc'] = ProjectAccountD3.objects.filter(d1__accountsort=1)
        context['pa_d3_out'] = ProjectAccountD3.objects.filter(d1__accountsort=2)
        context['pa_d3_trans'] = ProjectAccountD3.objects.filter(d1__accountsort=3)
        context['d2s'] = ProjectAccountD2.objects.all()
        for d1 in context['d2s']:
            context['d3_' + str(d1.id)] = ProjectAccountD3.objects.filter(d1=d1.id)
        project_id = self.get_project().id if self.get_project() else None
        context['pb_account'] = ProjectBankAccount.objects.filter(project=project_id)
        context['formset'] = ProjectCashBookFormSet(queryset=ProjectCashBook.objects.none(),
                                                    form_kwargs={'project': self.get_project()})
        return context

    def form_valid(self, form):
        formset = ProjectCashBookFormSet(self.request.POST, form_kwargs={'project': self.request.POST.get('project')})
        if formset.is_valid():
            for form in formset:
                instance = form.save(commit=False)
                instance.project = Project.objects.get(pk=self.request.POST.get('project'))
                instance.deal_date = self.request.POST.get('deal_date')
                instance.user = self.request.user
                instance.save()
        return super(ProjectCashInoutCV, self).form_valid(form)


class ProjectCashInoutUV(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = ProjectCashBook
    success_message = '해당 거래가 수정되었습니다.'
    fields = ('deal_date',)

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_success_url(self):
        project_query = '?project=' + self.request.POST.get('project')
        return reverse_lazy('ibs:cash-inout:project-index') + project_query

    def get_context_data(self, **kwargs):
        context = super(ProjectCashInoutUV, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['pa_d2_inc'] = ProjectAccountD2.objects.filter(accountsort=1)
        context['pa_d2_out'] = ProjectAccountD2.objects.filter(accountsort=2)
        context['pa_d2_trans'] = ProjectAccountD2.objects.filter(accountsort=3)
        context['pa_d3_inc'] = ProjectAccountD3.objects.filter(d1__accountsort=1)
        context['pa_d3_out'] = ProjectAccountD3.objects.filter(d1__accountsort=2)
        context['pa_d3_trans'] = ProjectAccountD3.objects.filter(d1__accountsort=3)
        context['d2s'] = ProjectAccountD2.objects.all()
        for d2 in context['d2s']:
            context['d3_' + str(d2.id)] = ProjectAccountD3.objects.filter(d2=d2.id)
        project_id = self.get_project().id if self.get_project() else None
        context['pb_account'] = ProjectBankAccount.objects.filter(project=project_id)
        context['formset'] = ProjectCashBookFormSet(queryset=ProjectCashBook.objects.none(),
                                                    form_kwargs={'project': self.get_project()})
        return context

    def form_valid(self, form):
        formset = ProjectCashBookFormSet(self.request.POST, form_kwargs={'project': self.request.POST.get('project')})
        if formset.is_valid():
            for form in formset:
                instance = form.save(commit=False)
                instance.project = Project.objects.get(pk=self.request.POST.get('project'))
                instance.deal_date = self.request.POST.get('deal_date')
                instance.recoder = self.request.user
                instance.save()
        return super(ProjectCashInoutUV, self).form_valid(form)


def ProjectCashInoutDV(request, *args, **kwargs):
    cash_inout = ProjectCashBook.objects.get(pk=kwargs['pk'])
    cash_inout.delete()
    return redirect(reverse_lazy('ibs:cash-inout:project-index'))


class SalesPaymentLV(LoginRequiredMixin, ListView, FormView):
    template_name = 'cash/project_payment_list.html'
    form_class = PaymentSearchForm
    paginate_by = 10

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_form_kwargs(self):
        kwargs = super(SalesPaymentLV, self).get_form_kwargs()
        kwargs['project'] = self.get_project()
        return kwargs

    def get_queryset(self):
        results = ProjectCashBook.objects.filter(project=self.get_project(), project_account_d3__in=(1, 5),
                                                 refund_contractor=None).order_by('-deal_date', '-id')

        if self.request.GET.get('sd'):
            results = results.filter(deal_date__gte=self.request.GET.get('sd'))

        if self.request.GET.get('ed'):
            results = results.filter(deal_date__lte=self.request.GET.get('ed'))

        if self.request.GET.get('ipo'):
            results = results.filter(Q(installment_order_id=self.request.GET.get('ipo')))

        if self.request.GET.get('ba'):
            results = results.filter(Q(bank_account__id=self.request.GET.get('ba')))

        if self.request.GET.get('up'):
            results = results.filter(
                Q(contract__isnull=True) &
                (Q(project_account_d2_id__in=(1, 2)) | Q(project_account_d3_id__in=(1, 2)))
            )

        if self.request.GET.get('q'):
            results = results.filter(
                Q(contract__contractor__name__icontains=self.request.GET.get('q', '')) |
                Q(trader__icontains=self.request.GET.get('q', '')) |
                Q(content__icontains=self.request.GET.get('q', '')) |
                Q(note__icontains=self.request.GET.get('q', ''))
            )
        return results

    def get_context_data(self, **kwargs):
        context = super(SalesPaymentLV, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['types'] = UnitType.objects.filter(project=self.get_project())

        total_budget = 0
        total_contract = 0
        total_paid = 0
        contract_num = []  # 타입별 세대수
        payment_type = []  # 타입별 수납금액
        for i, type in enumerate(context['types']):
            total_budget += type.average_price * type.num_unit
            contract_num.append(
                KeyUnit.objects.filter(project=self.get_project(), unit_type=type, contract__isnull=False).count())
            total_contract += type.average_price * contract_num[i]
            payment = ProjectCashBook.objects.filter(project=self.get_project(),
                                                     contract__keyunit__unit_type=type).aggregate(Sum('income'))
            payment_sum = payment.get('income__sum') if payment.get('income__sum') else 0
            payment_type.append(payment_sum)
            total_paid += payment_type[i]

        context['total_budget'] = total_budget
        context['total_contract'] = total_contract
        context['total_paid'] = total_paid
        context['contract_num'] = list(reversed(contract_num))
        context['payment_type'] = list(reversed(payment_type))
        return context


class SalesPaymentRegister(LoginRequiredMixin, FormView):
    model = ProjectCashBook
    form_class = PaymentForm
    template_name = 'cash/project_payment_form.html'

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_success_url(self):
        project = self.request.GET.get('project') if self.request.GET.get('project') else ''
        type = self.request.GET.get('type') if self.request.GET.get('type') else ''
        contract = self.request.GET.get('contract') if self.request.GET.get('contract') else ''
        q = self.request.GET.get('q') if self.request.GET.get('q') else ''
        project_query = '?project=' + project + '&type=' + type + '&contract=' + contract + '&q=' + q
        return reverse_lazy('ibs:cash-inout:payment-register') + project_query

    def get_form_kwargs(self):
        kwargs = super(SalesPaymentRegister, self).get_form_kwargs()
        kwargs['project'] = self.get_project()
        return kwargs

    def get_form(self, form_class=None):
        contract_id = self.request.GET.get('contract')
        contract = Contract.objects.get(pk=contract_id) if contract_id else None
        initial = {
            'project': self.get_project().id if self.get_project() else None,
            'project_account_d2': contract.order_group.sort if contract_id else None,
            'project_account_d3': contract.order_group.sort if contract_id else None,
            'contract': contract.id if contract_id else None
        }
        payment_id = self.request.GET.get('payment_id')
        if payment_id:
            payment = ProjectCashBook.objects.get(pk=payment_id)
            initial['deal_date'] = payment.deal_date
            initial['installment_order'] = payment.installment_order
            initial['income'] = payment.income
            initial['bank_account'] = payment.bank_account
            initial['trader'] = payment.trader
            initial['note'] = payment.note
        return self.form_class(
            self.get_project(),
            initial=initial
        )

    def get_context_data(self, **kwargs):
        context = super(SalesPaymentRegister, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['types'] = UnitType.objects.filter(project=self.get_project())
        context['today'] = datetime.today().date()
        contracts = Contract.objects.filter(project=self.get_project())
        if self.request.GET.get('type'):
            contracts = contracts.filter(keyunit__unit_type=self.request.GET.get('type'))
        context['contracts'] = contracts
        context['q_contracts'] = None
        q = self.request.GET.get('q')
        if q:
            context['q_contracts'] = Contract.objects.filter(Q(project=self.get_project()) &
                                                             (Q(serial_number__icontains=q) |
                                                              Q(contractor__name__icontains=q) |
                                                              Q(payments__trader__icontains=q))).distinct()

        context['this_contract'] = Contract.objects.get(pk=self.request.GET.get('contract')) \
            if self.request.GET.get('contract') else 0
        if not context['this_contract'] or context['this_contract'].activation:
            payments = ProjectCashBook.objects.filter(contract=context['this_contract'],
                                                      project_account_d3__in=(1, 5))
        else:
            payments = ProjectCashBook.objects.filter(contract=context['this_contract'])

        context['cont_payments'] = payments.order_by('deal_date', 'bank_account', 'trader', 'id')
        context['payment_sum'] = payments.aggregate(Sum('income')) if self.request.GET.get('contract') else None
        context['payment_orders'] = payment_orders = InstallmentPaymentOrder.objects.filter(project=self.get_project())
        if self.request.GET.get('payment_id'):
            context['this_payment'] = ProjectCashBook.objects.get(pk=self.request.GET.get('payment_id'))
        context['today'] = TODAY

        unpaid = 0  # 미납금
        pay_sum_by_order_list = []
        for po in context['payment_orders']:
            pay_sum_by_order = payments.filter(installment_order=po).aggregate(Sum('income'))  # 회차별 납부총액
            pay_sum_by_order_list.append(pay_sum_by_order['income__sum'] if pay_sum_by_order['income__sum'] else 0)
            unpaid += pay_sum_by_order['income__sum'] if pay_sum_by_order['income__sum'] else 0
        pay_sum_by_order_list = list(reversed(pay_sum_by_order_list))
        context['pay_sum_by_order_list'] = pay_sum_by_order_list

        # due_payment_by_order logic 구현
        contract = context['this_contract']
        try:
            unit = contract.keyunit.unitnumber
        except:
            unit = None
        unit_set = (self.get_project() and self.get_project().is_unit_set and unit)

        this_price = 0  # 해당 건 분양가
        payment_list = []  # 회차별 납부금액

        if contract:
            sales_price = SalesPriceByGT.objects.filter(project=self.get_project(),
                                                        order_group=contract.order_group,
                                                        unit_type=contract.unit_type)
            this_price = sales_price.get(
                unit_floor_type=contract.keyunit.houseunit.floor_type).price if unit_set else contract.unit_type.average_price

            # 1. 계약금
            down_order = payment_orders.filter(pay_sort='1')
            total_down = 0
            try:
                dp = DownPayment.objects.get(project=self.get_project(),
                                             order_group=contract.order_group,
                                             unit_type=contract.unit_type)
                pay_num = dp.number_payments
                down_payment = dp.payment_amount
            except:
                pay_num = payment_orders.filter(pay_sort='1').count()
                pn = round(pay_num / 2)
                down_payment = int(this_price * 0.1 / pn)

            for i, do in enumerate(down_order):
                down_amount = down_payment if i < pay_num else 0
                payment_list.append(down_amount)
                total_down += down_amount

                if i < 2 or (do.pay_due_date and do.pay_due_date < datetime.today().date()):
                    unpaid -= down_amount

            # 2. 중도금
            medium_order = payment_orders.filter(pay_sort='2')
            total_medium = 0
            for mo in medium_order:
                medium_amount = int(this_price * 0.1)
                payment_list.append(medium_amount)
                total_medium += medium_amount

                if mo.pay_due_date and mo.pay_due_date < datetime.today().date():
                    unpaid -= medium_amount
            # 3. 잔금
            balance_order = payment_orders.filter(pay_sort='3')
            for bo in balance_order:
                balance_amount = int((this_price - total_down - total_medium) / balance_order.count())
                payment_list.append(balance_amount)

                if bo.pay_due_date and bo.pay_due_date < datetime.today().date():
                    unpaid -= balance_amount
        else:
            for po in context['payment_orders']:
                payment_list.append(0)

        context['this_price'] = this_price
        context['payment_list'] = list(reversed(payment_list))
        context['second_pay'] = contract.contractor.contract_date + timedelta(days=30) if contract else None
        context['unpaid'] = unpaid

        return context

    def post(self, request, *args, **kwargs):
        payment_id = self.request.GET.get('payment_id')
        payment = ProjectCashBook.objects.get(pk=payment_id) if payment_id else None
        form = self.form_class(
            self.get_project(), request.POST, instance=payment) \
            if payment else \
            self.form_class(self.get_project(), request.POST)

        if form.is_valid():
            payment = form.save(commit=False)
            payment.sort = AccountSort.objects.get(pk=1)
            payment.recoder = self.request.user
            payment.save()
            return redirect(self.get_success_url())
        return render(request, 'cash/project_payment_form.html', {'form': form})


def paymentDeleteView(request, *args, **kwargs):
    qs = '?project=' + request.GET.get('project') + '&type=' + request.GET.get('type') + '&contract=' + request.GET.get(
        'contract')
    payment = ProjectCashBook.objects.get(pk=kwargs['pk'])
    payment.delete()
    return redirect(reverse_lazy('ibs:cash-inout:payment-register') + qs)
