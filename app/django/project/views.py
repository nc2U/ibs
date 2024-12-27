from django.db.models import Sum
from django.urls import reverse_lazy
from django.db.utils import IntegrityError
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView, TemplateView

from project.forms import (ProjectForm, OrderGroupFormSet, UnitTypeFormSet, UnitFloorTypeFormSet,
                           SalesPriceByGTFormSet, InstallmentPaymentOrderFormSet, DownPaymentFormSet,
                           SiteForm, SiteOwnerForm, SiteContractForm)
from company.models import Company
from contract.models import OrderGroup
from items.models import UnitType, UnitFloorType
from payment.models import SalesPriceByGT, InstallmentPaymentOrder, DownPayment
from project.models import Project, Site, SiteOwner, SiteContract, SiteOwnshipRelationship


class ProjectList(LoginRequiredMixin, ListView):
    model = Project
    paginate_by = 5


class ProjectCreate(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    success_message = '새 프로젝트가 등록되었습니다.'
    success_url = reverse_lazy('ibs:project:index')

    def form_valid(self, form):
        form.instance.company = Company.objects.first()
        return super(ProjectCreate, self).form_valid(form)


class ProjectUpdate(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    success_message = '해당 프로젝트의 수정사항이 적용되었습니다.'
    success_url = reverse_lazy('ibs:project:index')


class ProjectDelete(LoginRequiredMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('ibs:project:index')


class SettingsOrderGroup(LoginRequiredMixin, FormView):
    """차수 분류 등록"""
    form_class = OrderGroupFormSet
    template_name = 'project/settings_order_group.html'

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_context_data(self, **kwargs):
        context = super(SettingsOrderGroup, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['formset'] = OrderGroupFormSet(queryset=OrderGroup.objects.filter(project=self.get_project()))
        return context

    def post(self, request, *args, **kwargs):
        formset = OrderGroupFormSet(request.POST)

        if formset.is_valid():

            for form in formset:
                try:
                    instance = form.save(commit=False)
                    instance.project = self.get_project()
                    instance.save()
                except IntegrityError:
                    pass
            project_query = '?project=' + self.request.GET.get('project') if self.request.GET.get('project') else ''
            return redirect(reverse_lazy('ibs:project:set-ordergroup') + project_query)
        return render(request, 'project/settings_ordergroup.html', {'formset': formset})


class SettingsUnitType(LoginRequiredMixin, FormView):
    """타입 정보 등록"""
    form_class = UnitTypeFormSet
    template_name = 'project/settings_unit_type.html'

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_context_data(self, **kwargs):
        context = super(SettingsUnitType, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['formset'] = UnitTypeFormSet(queryset=UnitType.objects.filter(project=self.get_project()))
        return context

    def post(self, request, *args, **kwargs):
        formset = UnitTypeFormSet(request.POST)

        if formset.is_valid():

            for form in formset:
                try:
                    instance = form.save(commit=False)
                    instance.project = self.get_project()
                    instance.save()
                except IntegrityError:
                    pass
            project_query = '?project=' + self.request.GET.get('project') if self.request.GET.get('project') else ''
            return redirect(reverse_lazy('ibs:project:set-unit-type') + project_query)
        return render(request, 'project/settings_unittype.html', {'formset': formset})


class SettingsFloorType(LoginRequiredMixin, FormView):
    """층별 조건 등록"""
    form_class = UnitFloorTypeFormSet
    template_name = 'project/settings_floor_type.html'

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_context_data(self, **kwargs):
        context = super(SettingsFloorType, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['formset'] = UnitFloorTypeFormSet(queryset=UnitFloorType.objects.filter(project=self.get_project()))
        return context

    def post(self, request, *args, **kwargs):
        formset = UnitFloorTypeFormSet(request.POST)

        if formset.is_valid():

            for form in formset:
                try:
                    instance = form.save(commit=False)
                    instance.project = self.get_project()
                    instance.save()
                except IntegrityError:
                    pass
            project_query = '?project=' + self.request.GET.get('project') if self.request.GET.get('project') else ''
            return redirect(reverse_lazy('ibs:project:set-floor-type') + project_query)
        return render(request, 'project/settings_floor.html', {'formset': formset})


class SettingsSalesPrice(LoginRequiredMixin, TemplateView):
    """분양가 등록"""
    template_name = 'project/settings_sales_price.html'

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_context_data(self, **kwargs):
        context = super(SettingsSalesPrice, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['order_groups'] = OrderGroup.objects.filter(project=self.get_project())
        context['order_group'] = OrderGroup.objects.get(pk=self.request.GET.get('group')) \
            if self.request.GET.get('group') else OrderGroup.objects.first()
        context['types_sel'] = UnitType.objects.filter(project=self.get_project())
        if self.request.GET.get('type'):
            context['types'] = context['types_sel'].filter(pk=self.request.GET.get('type'))
        else:
            context['types'] = context['types_sel']
        context['floor_types'] = UnitFloorType.objects.filter(project=self.get_project())
        context['prices'] = SalesPriceByGT.objects.filter(project=self.get_project())
        return context

    def post(self, request, *args, **kwargs):
        og = OrderGroup.objects.get(pk=self.request.GET.get('group')) \
            if self.request.GET.get('group') else OrderGroup.objects.first()
        types_sel = UnitType.objects.filter(project=self.get_project())
        types = types_sel.filter(pk=self.request.GET.get('type')) if self.request.GET.get('type') else types_sel
        floor_types = UnitFloorType.objects.filter(project=self.get_project())

        for tp in types:
            for ft in floor_types:
                build_data = request.POST.get(
                    'sp_' + str(og.id) + '_' + str(tp.id) + '_' + str(ft.id) + '_bu')  # 입력된 건물가 데이터
                land_data = request.POST.get(
                    'sp_' + str(og.id) + '_' + str(tp.id) + '_' + str(ft.id) + '_la')  # 입력된 대지가 데이터
                tax_data = request.POST.get(
                    'sp_' + str(og.id) + '_' + str(tp.id) + '_' + str(ft.id) + '_ta')  # 입력된 부가세 데이터
                price_data = request.POST.get('sp_' + str(og.id) + '_' + str(tp.id) + '_' + str(ft.id))  # 입력된 분양가격 데이터
                price_build_data = build_data if build_data else None
                price_land_data = land_data if land_data else None
                price_tax_data = tax_data if tax_data else None
                price_data = price_data if price_data else None

                if price_build_data or price_land_data or price_tax_data or price_data:
                    price_id = request.POST.get(
                        'sp_' + str(og.id) + '_' + str(tp.id) + '_' + str(ft.id) + '_id')  # 기 등록 분양가격 데이터 아이디
                    if price_id:
                        sales_price = SalesPriceByGT(pk=price_id)
                        sales_price.project = self.get_project()
                        sales_price.order_group = og
                        sales_price.unit_type = tp
                        sales_price.unit_floor_type = ft
                        sales_price.price_build = price_build_data
                        sales_price.price_land = price_land_data
                        sales_price.price_tax = price_tax_data
                        sales_price.price = price_data
                    else:
                        sales_price = SalesPriceByGT(project=self.get_project(),
                                                     order_group=og,
                                                     unit_type=tp,
                                                     unit_floor_type=ft,
                                                     price_build=price_build_data,
                                                     price_land=price_land_data,
                                                     price_tax=price_tax_data,
                                                     price=price_data)
                    sales_price.save()

        type = request.GET.get('type') if request.GET.get('type') else ''
        query_string = '?project=' + str(self.get_project().id) + '&group=' + str(og.id) + '&type=' + type
        return redirect(reverse_lazy('ibs:project:set-sales-price') + query_string)


class SettingsPaymentOrder(LoginRequiredMixin, FormView):
    """납입회차 등록"""
    form_class = InstallmentPaymentOrderFormSet
    template_name = 'project/settings_payment_order.html'

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_context_data(self, **kwargs):
        context = super(SettingsPaymentOrder, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['formset'] = InstallmentPaymentOrderFormSet(
            queryset=InstallmentPaymentOrder.objects.filter(project=self.get_project()))
        return context

    def post(self, request, *args, **kwargs):
        formset = InstallmentPaymentOrderFormSet(request.POST)

        if formset.is_valid():

            for form in formset:
                try:
                    instance = form.save(commit=False)
                    instance.project = self.get_project()
                    instance.save()
                except IntegrityError:
                    pass
            project_query = '?project=' + self.request.GET.get('project') if self.request.GET.get('project') else ''
            return redirect(reverse_lazy('ibs:project:set-payment-order') + project_query)
        return render(request, 'project/settings_installment_order.html', {'formset': formset})


class SettingsDownPayment(LoginRequiredMixin, TemplateView):
    """차수/타입별 계약금 등록"""
    template_name = 'project/settings_down_payment.html'

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_context_data(self, **kwargs):
        context = super(SettingsDownPayment, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['formset'] = DownPaymentFormSet(queryset=DownPayment.objects.filter(project=self.get_project()))

        return context

    def post(self, request, *args, **kwargs):
        formset = DownPaymentFormSet(request.POST)

        if formset.is_valid():

            for form in formset:
                try:
                    instance = form.save(commit=False)
                    instance.project = self.get_project()
                    instance.save()
                except IntegrityError:
                    pass

        project = self.request.GET.get('project')
        query_string = '?project=' + project if project else ''
        return redirect(reverse_lazy('ibs:project:set-down-payment') + query_string)


class SiteManage(LoginRequiredMixin, ListView, FormView):
    model = Site
    form_class = SiteForm
    template_name = 'project/site_manage.html'
    paginate_by = 15

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_form(self, form_class=None):
        initial = {'project': self.get_project().pk if self.get_project() else None}
        if self.request.GET.get('site'):
            site = Site.objects.get(pk=self.request.GET.get('site'))
            initial['order'] = site.order
            initial['district'] = site.district
            initial['lot_number'] = site.lot_number
            initial['site_purpose'] = site.site_purpose
            initial['official_area'] = site.official_area
            initial['returned_area'] = site.returned_area
            initial['rights_restrictions'] = site.rights_restrictions
            initial['dup_issue_date'] = site.dup_issue_date
        return self.form_class(initial=initial)

    def get_queryset(self):
        return self.model.objects.filter(project=self.get_project())

    def get_context_data(self, **kwargs):
        context = super(SiteManage, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['total_site'] = Site.objects.filter(project=self.get_project())
        is_returned = self.get_project().is_returned_area if self.get_project() else None
        area = ['returned_area', 'returned_area__sum'] if is_returned else ['official_area', 'official_area__sum']
        context['total_area'] = context['total_site'].aggregate(Sum(area[0]))[area[1]]
        return context

    def post(self, request, *args, **kwargs):
        site = Site.objects.get(pk=request.GET.get('site')) if request.GET.get('site') else None
        form = self.form_class(request.POST, instance=site) if site else self.form_class(request.POST)

        if form.is_valid():
            form.save()  # PostForm 클래스에 정의된 save() 메소드 호출
            query_str = '?'
            if self.request.GET.get('page'):
                query_str += 'page=' + self.request.GET.get('page') + '&' if self.request.GET.get('page') else ''
            if self.request.GET.get('project'):
                query_str += 'project=' + self.request.GET.get('project')
            return redirect(reverse_lazy('ibs:project:site') + query_str)
        return render(request, 'project/site_manage.html', {'form': form})


def site_delete(*args, **kwargs):
    instance = Site.objects.get(pk=kwargs['pk'])
    instance.delete()
    query_str = '?' + str(args[0]).split('?')[1].split('\'')[0] if len(str(args[0]).split('?')) > 1 else ''
    return redirect(reverse_lazy('ibs:project:site') + query_str)


class SiteOwnerManage(LoginRequiredMixin, ListView, FormView):
    model = SiteOwner
    form_class = SiteOwnerForm
    template_name = 'project/site_owner_manage.html'
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
        kwargs = super(SiteOwnerManage, self).get_form_kwargs()
        kwargs['project'] = self.get_project()
        return kwargs

    def get_form(self, form_class=None):
        initial = {
            'project': self.get_project().pk if self.get_project() else None,
            'user': self.request.user
        }
        if self.request.GET.get('id'):
            site_owner = SiteOwner.objects.get(pk=self.request.GET.get('id'))
            initial['own_sort'] = site_owner.own_sort
            initial['owner'] = site_owner.owner
            initial['date_of_birth'] = site_owner.date_of_birth
            initial['phone1'] = site_owner.phone1
            initial['phone2'] = site_owner.phone2
            initial['zipcode'] = site_owner.zipcode
            initial['address1'] = site_owner.address1
            initial['address2'] = site_owner.address2
            initial['address3'] = site_owner.address3
            initial['sites'] = site_owner.sites.all()
        return self.form_class(self.get_project(), initial=initial)

    def get_context_data(self, **kwargs):
        context = super(SiteOwnerManage, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['total_owner'] = SiteOwner.objects.filter(project=self.get_project())
        total_area = SiteOwnshipRelationship.objects.filter(site__project=self.get_project())
        context['total_area'] = total_area.aggregate(Sum('owned_area'))['owned_area__sum']
        return context

    def get_queryset(self):
        return self.model.objects.filter(project=self.get_project()).distinct()

    def post(self, request, *args, **kwargs):
        s_owner = SiteOwner.objects.get(pk=request.GET.get('id')) if request.GET.get('id') else None
        form = self.form_class(self.get_project(), request.POST, instance=s_owner) if s_owner else self.form_class(
            self.get_project(), request.POST)

        if form.is_valid():
            form.save()  # 클래스에 정의된 save() 메소드 호출
            query_str = '?'
            if self.request.GET.get('page'):
                query_str += 'page=' + self.request.GET.get('page') + '&' if self.request.GET.get('page') else ''
            if self.request.GET.get('project'):
                query_str += 'project=' + self.request.GET.get('project')
            return redirect(reverse_lazy('ibs:project:site-owner') + query_str)
        return render(request, 'project/site_owner_manage.html', {'form': form})


def site_relationship_update(request):
    instance = SiteOwnshipRelationship.objects.get(pk=request.GET.get('pk'))
    if request.GET.get('ratio'):
        instance.ownership_ratio = request.GET.get('ratio')
    if request.GET.get('area'):
        instance.owned_area = request.GET.get('area')
    if request.GET.get('date'):
        instance.acquisition_date = request.GET.get('date')
    instance.save()
    query_str = '?'
    if request.GET.get('page'):
        query_str += 'page=' + request.GET.get('page') + '&'
    if request.GET.get('project'):
        query_str += 'project=' + request.GET.get('project')
    return redirect(reverse_lazy('ibs:project:site-owner') + query_str)


def site_relationship_delete(*args, **kwargs):
    instance = SiteOwnshipRelationship.objects.get(pk=kwargs['pk'])
    instance.delete()
    query_str = '?' + str(args[0]).split('?')[1].split('\'')[0] if len(str(args[0]).split('?')) > 1 else ''
    return redirect(reverse_lazy('ibs:project:site-owner') + query_str)


class SiteContractManage(LoginRequiredMixin, ListView, FormView):
    model = SiteContract
    form_class = SiteContractForm
    template_name = 'project/site_contract_manage.html'
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
        kwargs = super(SiteContractManage, self).get_form_kwargs()
        kwargs['project'] = self.get_project()
        return kwargs

    def get_form(self, form_class=None):
        initial = {
            'project': self.get_project().pk if self.get_project() else None,
            'user': self.request.user
        }
        if self.request.GET.get('id'):
            site_cont = SiteContract.objects.get(pk=self.request.GET.get('id'))
            initial['owner'] = site_cont.owner
            initial['contract_date'] = site_cont.contract_date
            initial['contract_area'] = site_cont.contract_area
            initial['total_price'] = site_cont.total_price
            initial['down_pay1'] = site_cont.down_pay1
            initial['down_pay1_is_paid'] = site_cont.down_pay1_is_paid
            initial['down_pay2'] = site_cont.down_pay2
            initial['down_pay2_date'] = site_cont.down_pay2_date
            initial['down_pay2_is_paid'] = site_cont.down_pay2_is_paid
            initial['inter_pay1'] = site_cont.inter_pay1
            initial['inter_pay1_date'] = site_cont.inter_pay1_date
            initial['inter_pay1_is_paid'] = site_cont.inter_pay1_is_paid
            initial['inter_pay2'] = site_cont.inter_pay2
            initial['inter_pay2_date'] = site_cont.inter_pay2_date
            initial['inter_pay2_is_paid'] = site_cont.inter_pay2_is_paid
            initial['remain_pay'] = site_cont.remain_pay
            initial['remain_pay_date'] = site_cont.remain_pay_date
            initial['remain_pay_is_paid'] = site_cont.remain_pay_is_paid
            initial['ownership_completion'] = site_cont.ownership_completion
            initial['acc_bank'] = site_cont.acc_bank
            initial['acc_number'] = site_cont.acc_number
            initial['acc_owner'] = site_cont.acc_owner
            initial['note'] = site_cont.note
        return self.form_class(self.get_project(), initial=initial)

    def get_queryset(self):
        return self.model.objects.filter(project=self.get_project())

    def get_context_data(self, **kwargs):
        context = super(SiteContractManage, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['total_contract'] = SiteContract.objects.filter(project=self.get_project()).count()
        # ta = []
        # context['total_cont_area'] = 0
        # paginator = Paginator(self.get_queryset(), self.paginate_by)
        # page = self.request.GET.get('page') if self.request.GET.get('page') else 1
        # paginate_queryset = paginator.page(page)
        # for i in paginate_queryset:
        #     own_area = SiteOwnshipRelationship.objects.filter(site_owner=i.owner).aggregate(Sum('owned_area'))
        #     own_area_sum = own_area['owned_area__sum'] if own_area['owned_area__sum'] else 0
        #     ta.append(own_area_sum)
        #     context['total_cont_area'] += own_area_sum
        # context['total_area'] = list(reversed(ta))
        return context

    def post(self, request, *args, **kwargs):
        s_cont = SiteContract.objects.get(pk=request.GET.get('id')) if request.GET.get('id') else None
        form = self.form_class(self.get_project(), request.POST, instance=s_cont) if s_cont else self.form_class(
            self.get_project(), request.POST)

        if form.is_valid():
            form.save()  # 클래스에 정의된 save() 메소드 호출
            query_str = '?'
            if self.request.GET.get('page'):
                query_str += 'page=' + self.request.GET.get('page') + '&' if self.request.GET.get('page') else ''
            if self.request.GET.get('project'):
                query_str += 'project=' + self.request.GET.get('project')
            return redirect(reverse_lazy('ibs:project:site-contract') + query_str)
        return render(request, 'project/site_contract_manage.html', {'form': form})


def site_contract_delete(*args, **kwargs):
    instance = SiteContract.objects.get(pk=kwargs['pk'])
    instance.delete()
    query_str = '?' + str(args[0]).split('?')[1].split('\'')[0] if len(str(args[0]).split('?')) > 1 else ''
    return redirect(reverse_lazy('ibs:project:site-contract') + query_str)
