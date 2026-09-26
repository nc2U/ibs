from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, FormView

from contract.models import OrderGroup, Contractor
from items.models import UnitType, BuildingUnit
from payment.models import SalesPriceByGT, InstallmentPaymentOrder, DownPayment
from project.models import Project
from .forms import SalesBillIssueForm
from .models import SalesBillIssue


def get_today_str():
    return timezone.localdate().strftime('%Y-%m-%d')


class BillManageView(LoginRequiredMixin, ListView, FormView):
    model = Contractor
    form_class = SalesBillIssueForm
    template_name = 'notice/contractor_bill_publish.html'

    def get_paginate_by(self, queryset):
        return self.request.GET.get('limit') if self.request.GET.get('limit') else 15

    def get_bill_issue(self):
        try:
            return SalesBillIssue.objects.get(project=self.get_project())
        except (SalesBillIssue.DoesNotExist, ObjectDoesNotExist, AttributeError):
            return None

    def get_project(self):
        try:
            project = self.request.user.staff_auth.default_project
        except (AttributeError, ObjectDoesNotExist):
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        if gp:
            found = Project.objects.filter(pk=gp).first()
            if found:
                project = found
        return project

    def get_form_kwargs(self):
        kwargs = super(BillManageView, self).get_form_kwargs()
        kwargs['project'] = self.get_project()
        return kwargs

    def get_form(self, form_class=None):
        initial = {}
        bill_issue = self.get_bill_issue()
        if bill_issue:
            initial['now_payment_order'] = bill_issue.now_payment_order
            initial['now_due_date'] = bill_issue.now_payment_order.pay_due_date
            initial['host_name'] = bill_issue.host_name
            initial['host_tel'] = bill_issue.host_tel
            initial['agency'] = bill_issue.agency
            initial['agency_tel'] = bill_issue.agency_tel
            initial['bank_account1'] = bill_issue.bank_account1
            initial['bank_number1'] = bill_issue.bank_number1
            initial['bank_host1'] = bill_issue.bank_host1
            initial['bank_account2'] = bill_issue.bank_account2
            initial['bank_number2'] = bill_issue.bank_number2
            initial['bank_host2'] = bill_issue.bank_host2
            initial['zipcode'] = bill_issue.zipcode
            initial['address1'] = bill_issue.address1
            initial['address2'] = bill_issue.address2
            initial['address3'] = bill_issue.address3
            initial['title'] = bill_issue.title
            initial['content'] = bill_issue.content

        return self.form_class(self.get_project(), initial=initial)

    def get_queryset(self):
        queryset = self.model.objects.filter(contract__project=self.get_project(), status='2') \
            .order_by('-contract_date', '-created')
        group = self.request.GET.get('group')
        type = self.request.GET.get('type')
        dong = self.request.GET.get('dong')
        order = self.request.GET.get('order')
        q = self.request.GET.get('q')

        if group:
            queryset = queryset.filter(contract__order_group=group)
        if type:
            queryset = queryset.filter(contract__key_unit__unit_type=type)
        if dong:
            queryset = queryset.filter(contract__key_unit__houseunit__building_unit=dong)
        order_list = ['contract_date', '-contract_date', 'contract__serial_number',
                      '-contract__serial_number', 'name', '-name']
        if order and order.isdigit() and 0 <= int(order) < len(order_list):
            queryset = queryset.order_by(order_list[int(order)])
        if q:
            queryset = queryset.filter(name__icontains=q)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(BillManageView, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staff_auth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['today'] = get_today_str()
        context['groups'] = OrderGroup.objects.filter(project=self.get_project())
        context['types'] = UnitType.objects.filter(project=self.get_project())
        context['dongs'] = BuildingUnit.objects.filter(project=self.get_project())
        context['bill_issue'] = self.get_bill_issue()
        context['contractor_count'] = self.get_queryset().count()

        # 계약자 별 총 납입금 계산
        paginator = Paginator(self.get_queryset(), self.get_paginate_by(self.get_queryset()))
        page = self.request.GET.get('page') if self.request.GET.get('page') else 1
        paginate_queryset = paginator.page(page)

        # 계약자별 납부상태 구하기 + 계약자별 현 회차 상태(완납회차 계산)
        bill_issue = self.get_bill_issue()
        now_pay_code = bill_issue.now_payment_order.pay_code if (bill_issue and bill_issue.now_payment_order) else 2

        total_pay_by_contract = []
        amounts = []
        paid_order = []
        for contractor in paginate_queryset:
            contract = contractor.contract
            unit_set = getattr(getattr(contract, 'key_unit', None), 'houseunit', None)
            group = contract.order_group
            type = contract.unit_type

            prices = SalesPriceByGT.objects.filter(project=self.get_project(), order_group=group,
                                                   unit_type=type)  # 타입별 분양가 그룹
            price = contract.unit_type.average_price  # 동호 미지정시 타입별 평균 분양가
            if unit_set:
                floor = unit_set.floor_type
                matched_price = prices.filter(unit_floor_type=floor).first()
                if matched_price:
                    price = matched_price

            all_pay_order = InstallmentPaymentOrder.objects.filter(
                project=self.get_project(),
                type_sort=contract.unit_type.sort
            ).exclude(excluded_order_groups=contract.order_group)
            now_pay = 0

            payment_by_cont = contract.payments.aggregate(
                total=Sum('accounting_entry__amount')
            )['total'] or 0
            total_pay_by_contract.append(payment_by_cont)

            pay_by_order = 0  # 회차별 납입액 합계
            payid_by = payment_by_cont  # 해당 계약건 총 기납입액
            pbo_string = '계약금미납'
            balance_order = all_pay_order.filter(pay_sort='3')
            price_val = getattr(price, 'price', 0) if hasattr(price, 'price') else (price or 0)

            for apo in all_pay_order:

                if apo.pay_sort == '1':  # 계약금일때
                    try:
                        dp = DownPayment.objects.get(project=self.get_project(),
                                                     order_group=contract.order_group,
                                                     unit_type=contract.unit_type)
                        down_payment = dp.payment_amount
                    except (DownPayment.DoesNotExist, ObjectDoesNotExist):
                        pay_num = all_pay_order.filter(pay_sort='1').count() or 1
                        pn = round(pay_num / 2) or 1
                        down_payment = int(price_val * 0.1 / pn)
                    if apo.pay_code <= now_pay_code:
                        now_pay += down_payment
                    pay_by_order += down_payment  # 회차별 납입액 가산
                    if payid_by >= pay_by_order:
                        pbo_string = apo.pay_name
                    else:
                        break

                if apo.pay_sort == '2':  # 중도금일때
                    medium_amount = int(price_val * 0.1)
                    pay_by_order += medium_amount  # 회차별 납입액 가산
                    if apo.pay_code <= now_pay_code:
                        now_pay += medium_amount
                    if payid_by >= pay_by_order:
                        pbo_string = apo.pay_name
                    else:
                        break

                if apo.pay_sort == '3':  # 잔금일때
                    bal_count = balance_order.count() or 1
                    balance_amount = int((price_val - pay_by_order) / bal_count)
                    pay_by_order += balance_amount  # 회차별 납입액 가산
                    if apo.pay_code <= now_pay_code:
                        now_pay += balance_amount
                    if payid_by >= pay_by_order:
                        pbo_string = apo.pay_name
                    else:
                        break

            paid_order.append(pbo_string)
            amounts.append(now_pay)
        context['total_pay_by_contract'] = list(reversed(total_pay_by_contract))
        context['amounts'] = list(reversed(amounts))
        context['paid_order'] = list(reversed(paid_order))

        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(self.get_project(), request.POST)

        if form.is_valid():
            with transaction.atomic():  # 트랜잭션

                if self.get_bill_issue():
                    if form.cleaned_data.get('now_due_date') != self.get_bill_issue().now_payment_order.pay_due_date:
                        now_due_order = InstallmentPaymentOrder.objects.get(pk=request.POST.get('now_payment_order'))
                        now_due_order.pay_due_date = form.cleaned_data.get('now_due_date')
                        now_due_order.save()
                    bill_issue = SalesBillIssue.objects.get(project=self.get_project())
                    bill_issue.project = self.get_project()
                    bill_issue.now_payment_order = form.cleaned_data.get('now_payment_order')
                    bill_issue.host_name = form.cleaned_data.get('host_name')
                    bill_issue.host_tel = form.cleaned_data.get('host_tel')
                    bill_issue.agency = form.cleaned_data.get('agency')
                    bill_issue.agency_tel = form.cleaned_data.get('agency_tel')
                    bill_issue.bank_account1 = form.cleaned_data.get('bank_account1')
                    bill_issue.bank_number1 = form.cleaned_data.get('bank_number1')
                    bill_issue.bank_host1 = form.cleaned_data.get('bank_host1')
                    bill_issue.bank_account2 = form.cleaned_data.get('bank_account2')
                    bill_issue.bank_number2 = form.cleaned_data.get('bank_number2')
                    bill_issue.bank_host2 = form.cleaned_data.get('bank_host2')
                    bill_issue.zipcode = form.cleaned_data.get('zipcode')
                    bill_issue.address1 = form.cleaned_data.get('address1')
                    bill_issue.address2 = form.cleaned_data.get('address2')
                    bill_issue.address3 = form.cleaned_data.get('address3')
                    bill_issue.title = form.cleaned_data.get('title')
                    bill_issue.content = form.cleaned_data.get('content')
                    bill_issue.creator = request.user
                else:
                    now_due_order = InstallmentPaymentOrder.objects.get(pk=request.POST.get('now_payment_order'))
                    now_due_order.pay_due_date = form.cleaned_data.get('now_due_date')
                    now_due_order.save()
                    bill_issue = SalesBillIssue(project=self.get_project(),
                                                now_payment_order=form.cleaned_data.get('now_payment_order'),
                                                host_name=form.cleaned_data.get('host_name'),
                                                host_tel=form.cleaned_data.get('host_tel'),
                                                agency=form.cleaned_data.get('agency'),
                                                agency_tel=form.cleaned_data.get('agency_tel'),
                                                bank_account1=form.cleaned_data.get('bank_account1'),
                                                bank_number1=form.cleaned_data.get('bank_number1'),
                                                bank_host1=form.cleaned_data.get('bank_host1'),
                                                bank_account2=form.cleaned_data.get('bank_account2'),
                                                bank_number2=form.cleaned_data.get('bank_number2'),
                                                bank_host2=form.cleaned_data.get('bank_host2'),
                                                zipcode=form.cleaned_data.get('zipcode'),
                                                address1=form.cleaned_data.get('address1'),
                                                address2=form.cleaned_data.get('address2'),
                                                address3=form.cleaned_data.get('address3'),
                                                title=form.cleaned_data.get('title'),
                                                content=form.cleaned_data.get('content'),
                                                creator=request.user)
                bill_issue.save()
                page = '?page=' + self.request.GET.get('page') if self.request.GET.get('page') else ''
                return redirect(reverse_lazy('ibs:notice:bill') + page)

        return render(request, 'notice/contractor_bill_publish.html', {'form': form})
