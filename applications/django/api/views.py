from django.db.models import Sum, Count, F
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django_filters.rest_framework import FilterSet
from django_filters import ChoiceFilter, ModelChoiceFilter, DateFilter, BooleanFilter

from .permission import *
from .pagination import *
from .serializers import *

from accounts.models import User, Profile, Todo
from company.models import Company, Department, Position, Staff
from project.models import (Project, UnitType, UnitFloorType,
                            KeyUnit, BuildingUnit, HouseUnit, ProjectBudget,
                            Site, SiteOwner, SiteOwnshipRelationship, SiteContract)
from rebs.models import (AccountSort, AccountSubD1, AccountSubD2, AccountSubD3,
                         ProjectAccountD1, ProjectAccountD2, WiseSaying)
from cash.models import (BankCode, CompanyBankAccount, ProjectBankAccount,
                         CashBook, ProjectCashBook, SalesPriceByGT,
                         InstallmentPaymentOrder, DownPayment, OverDueRule)
from contract.models import (OrderGroup, Contract, Contractor,
                             ContractorAddress, ContractorContact, ContractorRelease)
from notice.models import SalesBillIssue
from document.models import Group, Board, Category, LawsuitCase, Post, Image, Link, File, Comment, Tag


class ApiIndex(generics.GenericAPIView):
    name = 'api-index'
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        api = 'api:'
        return Response({
            'user': reverse(api + UserList.name, request=request),
            'profile': reverse(api + ProfileList.name, request=request),
            'todo': reverse(api + TodoList.name, request=request),
            'company': reverse(api + CompanyList.name, request=request),
            'department': reverse(api + DepartmentList.name, request=request),
            'position': reverse(api + PositionList.name, request=request),
            'staff': reverse(api + StaffList.name, request=request),
            'account-sort': reverse(api + AccountSortList.name, request=request),
            'account-depth1': reverse(api + AccountSubD1List.name, request=request),
            'account-depth2': reverse(api + AccountSubD2List.name, request=request),
            'account-depth3': reverse(api + AccountSubD3List.name, request=request),
            'project-acc-d1': reverse(api + ProjectAccountD1List.name, request=request),
            'project-acc-d2': reverse(api + ProjectAccountD2List.name, request=request),
            'project': reverse(api + ProjectList.name, request=request),
            'type': reverse(api + UnitTypeList.name, request=request),
            'floor': reverse(api + UnitFloorTypeList.name, request=request),
            'key-unit': reverse(api + KeyUnitList.name, request=request),
            'bldg-unit': reverse(api + BuildingUnitList.name, request=request),
            'house-unit': reverse(api + HouseUnitList.name, request=request),
            # 'budget': reverse(api + ProjectBudgetList.name, request=request),
            # 'site': reverse(api + SiteList.name, request=request),
            # 'site-owner': reverse(api + SiteOwnerList.name, request=request),
            # 'site-relation': reverse(api + RelationList.name, request=request),
            # 'site-contract': reverse(api + SiteContractList.name, request=request),
            # 'bank-code': reverse(api + BankCodeList.name, request=request),
            'com-bank': reverse(api + ComBankAccountList.name, request=request),
            'cashbook': reverse(api + CashBookList.name, request=request),
            'project-bank': reverse(api + ProjectBankAccountList.name, request=request),
            'project-cashbook': reverse(api + ProjectCashBookList.name, request=request),
            'payment-list': reverse(api + PaymentList.name, request=request),
            'payment-sum': reverse(api + PaymentSummary.name, request=request),
            'cont-count': reverse(api + NumContractByType.name, request=request),
            'price': reverse(api + SalesPriceList.name, request=request),
            'pay-order': reverse(api + InstallmentOrderList.name, request=request),
            'down-payment': reverse(api + DownPaymentList.name, request=request),
            # 'over-due-rule': reverse(api + OverDueRuleList.name, request=request),
            'order-group': reverse(api + OrderGroupList.name, request=request),
            'contract': reverse(api + ContractList.name, request=request),
            'subs-sum': reverse(api + SubsSummaryList.name, request=request),
            'cont-sum': reverse(api + ContSummaryList.name, request=request),
            # 'contractor': reverse(api + ContractorList.name, request=request),
            # 'contractor-address': reverse(api + ContAddressList.name, request=request),
            # 'contractor-contact': reverse(api + ContContactList.name, request=request),
            # 'contractor-release': reverse(api + ContReleaseList.name, request=request),
            # 'sales-bill-issue': reverse(api + BillIssueList.name, request=request),
            # 'group': reverse(api + GroupList.name, request=request),
            # 'board': reverse(api + BoardList.name, request=request),
            # 'category': reverse(api + CategoryList.name, request=request),
            # 'suitcase': reverse(api + LawSuitCaseList.name, request=request),
            # 'post': reverse(api + PostList.name, request=request),
            # 'image': reverse(api + ImageList.name, request=request),
            # 'link': reverse(api + LinkList.name, request=request),
            # 'file': reverse(api + FileList.name, request=request),
            # 'comment': reverse(api + CommentList.name, request=request),
            # 'tag': reverse(api + TagList.name, request=request),
            'wise-say': reverse(api + WiseSayList.name, request=request),
        })


# Accounts --------------------------------------------------------------------------
class UserList(generics.ListCreateAPIView):
    name = 'user-list'
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'user-detail'
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnSelfOrReadOnly)


class ProfileList(generics.ListCreateAPIView):
    name = 'profile-list'
    queryset = Profile.objects.all()
    serializer_class = ProfileInUserSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOnly)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProfileDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'profile-detail'
    queryset = Profile.objects.all()
    serializer_class = ProfileInUserSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOnly)


class TodoList(generics.ListCreateAPIView):
    name = 'todo-list'
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsOwnerOnly)
    filter_fields = ('user', 'soft_deleted')
    search_fields = ('title',)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TodoDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'todo-detail'
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOnly)


# Company --------------------------------------------------------------------------
class CompanyList(generics.ListCreateAPIView):
    name = 'company-list'
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperUserOrReadOnly)


class CompanyDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'company-detail'
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class DepartmentList(generics.ListCreateAPIView):
    name = 'depart-list'
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class DepartmentDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'depart-detail'
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class PositionList(generics.ListCreateAPIView):
    name = 'position-list'
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class PositionDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'position-detail'
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class StaffList(generics.ListCreateAPIView):
    name = 'staff-list'
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class StaffDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'staff-detail'
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# Rebs --------------------------------------------------------------------------
class AccountSortList(generics.ListAPIView):
    name = 'acc_sort-list'
    queryset = AccountSort.objects.all()
    serializer_class = AccountSortSerializer


class AccountSortDetail(generics.RetrieveAPIView):
    name = 'acc_sort-detail'
    queryset = AccountSort.objects.all()
    serializer_class = AccountSortSerializer


class AccountSubD1List(generics.ListAPIView):
    name = 'acc_d1-list'
    queryset = AccountSubD1.objects.all()
    serializer_class = AccountSubD1Serializer
    filter_fields = ('accountsort',)


class AccountSubD1Detail(generics.RetrieveAPIView):
    name = 'acc_d1-detail'
    queryset = AccountSubD1.objects.all()
    serializer_class = AccountSubD1Serializer


class AccountSubD2List(generics.ListAPIView):
    name = 'acc_d2-list'
    queryset = AccountSubD2.objects.all()
    serializer_class = AccountSubD2Serializer
    pagination_class = PageNumberPaginationTwenty
    filter_fields = ('d1__accountsort', 'd1')


class AccountSubD2Detail(generics.RetrieveAPIView):
    name = 'acc_d2-detail'
    queryset = AccountSubD2.objects.all()
    serializer_class = AccountSubD2Serializer


class AccountSubD3List(generics.ListAPIView):
    name = 'acc_d3-list'
    queryset = AccountSubD3.objects.all()
    serializer_class = AccountSubD3Serializer
    pagination_class = PageNumberPaginationTwoHundred
    filter_fields = ('d2__d1__accountsort', 'd2__d1', 'd2')


class AccountSubD3Detail(generics.RetrieveAPIView):
    name = 'acc_d3-detail'
    queryset = AccountSubD3.objects.all()
    serializer_class = AccountSubD3Serializer


class ProjectAccountD1List(generics.ListAPIView):
    name = 'project_acc_d1-list'
    queryset = ProjectAccountD1.objects.all()
    pagination_class = PageNumberPaginationTwenty
    serializer_class = ProjectAccountD1Serializer
    filter_fields = ('sort',)


class ProjectAccountD1Detail(generics.RetrieveAPIView):
    name = 'project_acc_d1-detail'
    queryset = ProjectAccountD1.objects.all()
    serializer_class = ProjectAccountD1Serializer


class ProjectAccountD2List(generics.ListAPIView):
    name = 'project_acc_d2-list'
    queryset = ProjectAccountD2.objects.all()
    pagination_class = PageNumberPaginationOneHundred
    serializer_class = ProjectAccountD2Serializer
    filter_fields = ('d1', 'd1__sort')


class ProjectAccountD2Detail(generics.RetrieveAPIView):
    name = 'project_acc_d2-detail'
    queryset = ProjectAccountD2.objects.all()
    serializer_class = ProjectAccountD2Serializer


# Project --------------------------------------------------------------------------
class ProjectList(generics.ListCreateAPIView):
    name = 'project-list'
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperUserOrReadOnly)


class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'project-detail'
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperUserOrReadOnly)


class UnitTypeList(generics.ListCreateAPIView):
    name = 'unittype-list'
    queryset = UnitType.objects.all()
    serializer_class = UnitTypeSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filter_fields = ('project',)
    search_fields = ('name',)


class UnitTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'unittype-detail'
    queryset = UnitType.objects.all()
    serializer_class = UnitTypeSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class UnitFloorTypeList(generics.ListCreateAPIView):
    name = 'floortype-list'
    queryset = UnitFloorType.objects.all()
    serializer_class = UnitFloorTypeSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filter_fields = ('project',)
    search_fields = ('alias_name',)


class UnitFloorTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'floortype-detail'
    queryset = UnitFloorType.objects.all()
    serializer_class = UnitFloorTypeSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class BuildingUnitList(generics.ListCreateAPIView):
    name = 'bldg-list'
    queryset = BuildingUnit.objects.all()
    serializer_class = BuildingUnitSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filter_fields = ('project',)
    search_fields = ('name',)


class BuildingUnitDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'bldg-detail'
    queryset = BuildingUnit.objects.all()
    serializer_class = BuildingUnitSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class KeyUnitList(generics.ListCreateAPIView):
    name = 'key_unit-list'
    queryset = KeyUnit.objects.all()
    serializer_class = KeyUnitSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filter_fields = ('project', 'unit_type')


class KeyUnitDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'key_unit-detail'
    queryset = KeyUnit.objects.all()
    serializer_class = KeyUnitSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class HouseUnitList(generics.ListCreateAPIView):
    name = 'unit-list'
    queryset = HouseUnit.objects.all()
    serializer_class = HouseUnitSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationTwoHundred
    filter_fields = ('project', 'unit_type', 'floor_type', 'building_unit',
                     'bldg_line', 'floor_no', 'is_hold')
    search_fields = ('hold_reason',)


class HouseUnitDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'unit-detail'
    queryset = HouseUnit.objects.all()
    serializer_class = HouseUnitSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class ProjectBudgetList(generics.ListCreateAPIView):
#     name = 'projectbudget-list'
#     queryset = ProjectBudget.objects.all()
#     serializer_class = ProjectBudgetSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#
# class ProjectBudgetDetail(generics.ListCreateAPIView):
#     name = 'projectbudget-detail'
#     queryset = ProjectBudget.objects.all()
#     serializer_class = ProjectBudgetSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class SiteList(generics.ListCreateAPIView):
#     name = 'site-list'
#     queryset = Site.objects.all()
#     serializer_class = SiteSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#
# class SiteDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'site-detail'
#     queryset = Site.objects.all()
#     serializer_class = SiteSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class SiteOwnerList(generics.ListCreateAPIView):
#     name = 'siteowner-list'
#     queryset = SiteOwner.objects.all()
#     serializer_class = SiteOwnerSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#
# class SiteOwnerDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'siteowner-detail'
#     queryset = SiteOwner.objects.all()
#     serializer_class = SiteOwnerSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class RelationList(generics.ListCreateAPIView):
#     name = 'relation-list'
#     queryset = SiteOwnshipRelationship.objects.all()
#     serializer_class = SiteOwnshipRelationSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#
# class RelationDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'relation-detail'
#     queryset = SiteOwnshipRelationship.objects.all()
#     serializer_class = SiteOwnshipRelationSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class SiteContractList(generics.ListCreateAPIView):
#     name = 'sitecontract-list'
#     queryset = SiteContract.objects.all()
#     serializer_class = SiteContractSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#
# class SiteContractDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'sitecontract-detail'
#     queryset = SiteContract.objects.all()
#     serializer_class = SiteContractSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# # Cash --------------------------------------------------------------------------
# class BankCodeList(generics.ListAPIView):
#     name = 'bankcode-list'
#     queryset = BankCode.objects.all()
#     serializer_class = BankCodeSerializer
#
#
# class BankCodeDetail(generics.ListAPIView):
#     name = 'bankcode-detail'
#     queryset = BankCode.objects.all()
#     serializer_class = BankCodeSerializer


class ComBankAccountList(generics.ListCreateAPIView):
    name = 'com_bank-list'
    queryset = CompanyBankAccount.objects.all()
    serializer_class = CompanyBankAccountSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class ComBankAccountDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'com_bank-detail'
    queryset = CompanyBankAccount.objects.all()
    serializer_class = CompanyBankAccountSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class CashBookFilterSet(FilterSet):
    from_deal_date = DateFilter(field_name='deal_date', lookup_expr='gte', label='납부일자부터')
    to_deal_date = DateFilter(field_name='deal_date', lookup_expr='lte', label='납부일자까지')

    class Meta:
        model = CashBook
        fields = ('company', 'from_deal_date', 'to_deal_date', 'sort',
                  'account_d1', 'account_d2', 'account_d3', 'bank_account')


class CashBookList(generics.ListCreateAPIView):
    name = 'cashbook-list'
    queryset = CashBook.objects.all()
    serializer_class = CashBookSerializer
    pagination_class = PageNumberPaginationFifteen
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filter_class = CashBookFilterSet
    search_fields = ('content', 'trader', 'note')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CashBookDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'cashbook-detail'
    queryset = CashBook.objects.all()
    serializer_class = CashBookSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class ProjectBankAccountList(generics.ListCreateAPIView):
    name = 'project_bank-list'
    queryset = ProjectBankAccount.objects.all()
    serializer_class = ProjectBankAccountSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filter_fields = ('project',)


class ProjectBankAccountDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'project_bank-detail'
    queryset = ProjectBankAccount.objects.all()
    serializer_class = ProjectBankAccountSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class ProjectCashBookFilterSet(FilterSet):
    from_deal_date = DateFilter(field_name='deal_date', lookup_expr='gte', label='납부일자부터')
    to_deal_date = DateFilter(field_name='deal_date', lookup_expr='lte', label='납부일자까지')
    no_contract = BooleanFilter(field_name='contract', lookup_expr='isnull', label='미등록')

    class Meta:
        model = ProjectCashBook
        fields = ('project', 'sort', 'project_account_d1', 'project_account_d2',
                  'is_release', 'from_deal_date', 'to_deal_date', 'installment_order',
                  'bank_account', 'is_contract_payment', 'contract', 'no_contract')


class ProjectCashBookList(generics.ListCreateAPIView):
    name = 'project_cashbook-list'
    queryset = ProjectCashBook.objects.all()
    serializer_class = ProjectCashBookSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationFifteen
    filter_class = ProjectCashBookFilterSet
    search_fields = ('contract__contractor__name', 'content', 'trader', 'note')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProjectCashBookDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'project_cashbook-detail'
    queryset = ProjectCashBook.objects.all()
    serializer_class = ProjectCashBookSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class PaymentList(ProjectCashBookList):
    name = 'payment-list'
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return ProjectCashBook.objects.filter(project_account_d2__in=(1, 2), is_release=False)


class PaymentDetail(ProjectCashBookDetail):
    name = 'payment-detail'
    serializer_class = PaymentSerializer


class PaymentSummary(generics.ListAPIView):
    name = 'payment-sum'
    serializer_class = PaymentSummarySerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filter_fields = ('project',)

    def get_queryset(self):
        return Contract.objects.filter(activation=True, contractor__status=2) \
            .annotate(income=F('projectcashbook__income')) \
            .values('unit_type', 'income') \
            .values('unit_type') \
            .annotate(type_total=Sum('income'))


class NumContractByType(generics.ListAPIView):
    name = 'cont-count'
    serializer_class = NumContractByTypeSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filter_fields = ('project',)

    def get_queryset(self):
        return Contract.objects.filter(activation=True, contractor__status=2) \
            .values('unit_type') \
            .annotate(num_cont=Count('unit_type'))


class SalesPriceList(generics.ListCreateAPIView):
    name = 'price-list'
    queryset = SalesPriceByGT.objects.all()
    serializer_class = SalesPriceSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filter_fields = ('project', 'order_group', 'unit_type')


class SalesPriceDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'price-detail'
    queryset = SalesPriceByGT.objects.all()
    serializer_class = SalesPriceSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class InstallmentOrderList(generics.ListCreateAPIView):
    name = 'install_order-list'
    queryset = InstallmentPaymentOrder.objects.all()
    serializer_class = InstallmentOrderSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationTwenty
    filter_fields = ('project', 'pay_sort', 'is_pm_cost')
    search_fields = ('pay_name', 'alias_name')


class InstallmentOrderDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'install_order-detail'
    queryset = InstallmentPaymentOrder.objects.all()
    serializer_class = InstallmentOrderSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class DownPaymentList(generics.ListCreateAPIView):
    name = 'downpay-list'
    queryset = DownPayment.objects.all()
    serializer_class = DownPaymentSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationTwenty
    filter_fields = ('project', 'order_group', 'unit_type')


class DownPaymentDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'downpay-detail'
    queryset = DownPayment.objects.all()
    serializer_class = DownPaymentSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class OverDueRuleList(generics.ListCreateAPIView):
#     name = 'over_due_rule-list'
#     queryset = OverDueRule.objects.all()
#     serializer_class = OverDueRuleSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#
# class OverDueRuleDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'over_due_rule-detail'
#     queryset = OverDueRule.objects.all()
#     serializer_class = OverDueRuleSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# Contract --------------------------------------------------------------------------
class OrderGroupList(generics.ListCreateAPIView):
    name = 'order_group-list'
    queryset = OrderGroup.objects.all()
    serializer_class = OrderGroupSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filter_fields = ('project', 'sort')
    search_fields = ('order_group_name',)


class OrderGroupDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'order_group-detail'
    queryset = OrderGroup.objects.all()
    serializer_class = OrderGroupSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class ContractFilter(FilterSet):
    keyunit__houseunit__building_unit = ModelChoiceFilter(queryset=BuildingUnit.objects.all(), label='동(건물)')
    contractor__status = ChoiceFilter(field_name='contractor__status', choices=Contractor.STATUS_CHOICES, label='현재상태')
    contractor__is_registed = BooleanFilter(field_name='contractor__is_registed', label='인가등록여부')
    from_contract_date = DateFilter(field_name='contractor__contract_date', lookup_expr='gte', label='계약일자부터')
    to_contract_date = DateFilter(field_name='contractor__contract_date', lookup_expr='lte', label='계약일자까지')

    class Meta:
        model = Contract
        fields = ('project', 'order_group', 'activation', 'unit_type',
                  'keyunit__houseunit__building_unit', 'contractor__status',
                  'contractor__is_registed', 'from_contract_date', 'to_contract_date')


class ContractList(generics.ListCreateAPIView):
    name = 'contract-list'
    queryset = Contract.objects.all()
    serializer_class = ContractListSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filter_class = ContractFilter
    search_fields = ('serial_number', 'contractor__name', 'contractor__note')
    ordering_fields = (
        'created_at', 'contractor__contract_date', 'serial_number',
        'contractor__name', 'projectcashbook__trader')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ContractDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'contract-detail'
    queryset = Contract.objects.all()
    serializer_class = ContractListSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class SubsSummaryList(generics.ListAPIView):
    name = 'subs-summary'
    serializer_class = SubsSummarySerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filter_fields = ('project',)

    def get_queryset(self):
        return Contract.objects.filter(activation=True, contractor__status=1) \
            .values('unit_type') \
            .annotate(num_cont=Count('unit_type'))


class ContSummaryList(generics.ListAPIView):
    name = 'cont-summary'
    serializer_class = ContSummarySerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filter_fields = ('project',)

    def get_queryset(self):
        return Contract.objects.filter(activation=True, contractor__status=2) \
            .values('order_group', 'unit_type') \
            .annotate(num_cont=Count('order_group'))


# class ContractorList(generics.ListCreateAPIView):
#     name = 'contractor-list'
#     queryset = Contractor.objects.all()
#     serializer_class = ContractorSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)
#
#
# class ContractorDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'contractor-detail'
#     queryset = Contractor.objects.all()
#     serializer_class = ContractorSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#
# class ContAddressList(generics.ListCreateAPIView):
#     name = 'cont_address-list'
#     queryset = ContractorAddress.objects.all()
#     serializer_class = ContractorAddressSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)
#
#
# class ContAddressDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'cont_address-detail'
#     queryset = ContractorAddress.objects.all()
#     serializer_class = ContractorAddressSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#
# class ContContactList(generics.ListCreateAPIView):
#     name = 'contact-list'
#     queryset = ContractorContact.objects.all()
#     serializer_class = ContractorContactSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)
#
#
# class ContContactDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'contact-detail'
#     queryset = ContractorContact.objects.all()
#     serializer_class = ContractorContactSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class ContReleaseList(generics.ListCreateAPIView):
#     name = 'release-list'
#     queryset = ContractorRelease.objects.all()
#     serializer_class = ContractorReleaseSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)
#
#
# class ContReleaseDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'release-detail'
#     queryset = ContractorRelease.objects.all()
#     serializer_class = ContractorReleaseSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class BillIssueList(generics.ListCreateAPIView):
#     name = 'bill_issue-list'
#     queryset = SalesBillIssue.objects.all()
#     serializer_class = SallesBillIssueSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)
#
#
# class BillIssueDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'bill_issue-detail'
#     queryset = SalesBillIssue.objects.all()
#     serializer_class = SallesBillIssueSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#
# # Document --------------------------------------------------------------------------
# class GroupList(generics.ListCreateAPIView):
#     name = 'group-list'
#     queryset = Group.objects.all()
#     serializer_class = GroupSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#
# class GroupDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'group-detail'
#     queryset = Group.objects.all()
#     serializer_class = GroupSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#
# class BoardList(generics.ListCreateAPIView):
#     name = 'board-list'
#     queryset = Board.objects.all()
#     serializer_class = BoardSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#
# class BoardDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'board-detail'
#     queryset = Board.objects.all()
#     serializer_class = BoardSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class CategoryList(generics.ListCreateAPIView):
#     name = 'category-list'
#     queryset = Category.objects.all()
#     serializer_class = CategorySerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#
# class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'category-detail'
#     queryset = Category.objects.all()
#     serializer_class = CategorySerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class LawSuitCaseList(generics.ListCreateAPIView):
#     name = 'suitcase-list'
#     queryset = LawsuitCase.objects.all()
#     serializer_class = LawSuitCaseSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)
#
#
# class LawSuitCaseDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'suitcase-detail'
#     queryset = LawsuitCase.objects.all()
#     serializer_class = LawSuitCaseSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class PostList(generics.ListCreateAPIView):
#     name = 'post-list'
#     queryset = Post.objects.all()
#     serializer_class = PostSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)
#
#
# class PostDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'post-detail'
#     queryset = Post.objects.all()
#     serializer_class = PostSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class ImageList(generics.ListCreateAPIView):
#     name = 'image-list'
#     queryset = Image.objects.all()
#     serializer_class = ImageSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class ImageDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'image-detail'
#     queryset = Image.objects.all()
#     serializer_class = ImageSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class LinkList(generics.ListCreateAPIView):
#     name = 'link-list'
#     queryset = Link.objects.all()
#     serializer_class = LinkSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#
# class LinkDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'link-detail'
#     queryset = Link.objects.all()
#     serializer_class = LinkSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class FileList(generics.ListCreateAPIView):
#     name = 'file-list'
#     queryset = File.objects.all()
#     serializer_class = FileSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#
# class FileDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'file-detail'
#     queryset = File.objects.all()
#     serializer_class = FileSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class CommentList(generics.ListCreateAPIView):
#     name = 'comment-list'
#     queryset = Comment.objects.all()
#     serializer_class = CommentSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)
#
#
# class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'comment-detail'
#     queryset = Comment.objects.all()
#     serializer_class = CommentSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# class TagList(generics.ListCreateAPIView):
#     name = 'tag-list'
#     queryset = Tag.objects.all()
#     serializer_class = TagSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#
#
# class TagDetail(generics.RetrieveUpdateDestroyAPIView):
#     name = 'tag-detail'
#     queryset = Tag.objects.all()
#     serializer_class = TagSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


# Etc --------------------------------------------------------------------------
class WiseSayList(generics.ListCreateAPIView):
    name = 'wise-say-list'
    queryset = WiseSaying.objects.all()
    serializer_class = WiseSaySerializer
    permissions_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class WiseSayDetail(generics.RetrieveUpdateDestroyAPIView):
    name = 'wise-say-detail'
    queryset = WiseSaying.objects.all()
    serializer_class = WiseSaySerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
