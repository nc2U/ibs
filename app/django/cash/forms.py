from django import forms
from django.forms.models import modelformset_factory

from .models import CompanyBankAccount, CashBook, ProjectBankAccount, ProjectCashBook
from payment.models import InstallmentPaymentOrder
from ibs.models import ProjectAccountD2, ProjectAccountD3

CashBookFormSet = modelformset_factory(
    CashBook,
    fields=('sort', 'account_d1', 'account_d3', 'content', 'trader',
            'bank_account', 'income', 'outlay', 'evidence', 'note'),
    extra=1
)


class CashSearchForm(forms.Form):
    s_date = forms.DateField(required=False, label='거래 기간')
    e_date = forms.DateField(required=False)
    SORT_CHOICES = (('', '전체'), ('1', '입금'), ('2', '출금'), ('3', '대체'))
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False, label='구분')
    account_d1_CHOICES = (('', '전체'), ('1', '자산'), ('2', '부채'), ('3', '자본'), ('4', '수익'), ('5', '비용'), ('6', '대체'))
    account_d1 = forms.ChoiceField(choices=account_d1_CHOICES, required=False)
    bank_account = forms.ModelChoiceField(queryset=CompanyBankAccount.objects.all(), required=False)
    search_word = forms.CharField(max_length=20, required=False, label='검색어')


class ProjectCashBookForm(forms.ModelForm):
    class Meta:
        model = ProjectCashBook
        fields = ('sort', 'project_account_d2', 'project_account_d3',
                  'content', 'trader', 'bank_account', 'income', 'outlay', 'note')

    def __init__(self, project, *args, **kwargs):
        super(ProjectCashBookForm, self).__init__(*args, **kwargs)
        self.fields['bank_account'].queryset = ProjectBankAccount.objects.filter(project=project)


ProjectCashBookFormSet = modelformset_factory(model=ProjectCashBook, form=ProjectCashBookForm, extra=1)


class ProjectCashSearchForm(forms.Form):
    sdate = forms.DateField(required=False, label='거래 기간')
    edate = forms.DateField(required=False)
    SORT_CHOICES = (('', '전체'), ('1', '입금'), ('2', '출금'), ('3', '대체'))
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False, label='구분')
    d2 = forms.ModelChoiceField(queryset=ProjectAccountD2.objects.all(), required=False)
    d3 = forms.ModelChoiceField(queryset=ProjectAccountD3.objects.all(), required=False)
    bank_acc = forms.ModelChoiceField(queryset=None, required=False)
    q = forms.CharField(max_length=20, required=False, label='검색어')

    def __init__(self, project, *args, **kwargs):
        super(ProjectCashSearchForm, self).__init__(*args, **kwargs)
        self.fields['bank_acc'].queryset = ProjectBankAccount.objects.filter(project=project)


class PaymentSearchForm(forms.Form):
    sd = forms.DateField(required=False, label='거래 기간')
    ed = forms.DateField(required=False)
    ipo = forms.ModelChoiceField(queryset=None, required=False)
    ba = forms.ModelChoiceField(queryset=None, required=False)
    up = forms.BooleanField(initial=False, required=False, label='미등록 수납대금')
    q = forms.CharField(max_length=20, required=False, label='검색어')

    def __init__(self, project, *args, **kwargs):
        super(PaymentSearchForm, self).__init__(*args, **kwargs)
        self.fields['ipo'].queryset = InstallmentPaymentOrder.objects.filter(project=project)
        self.fields['ipo'].empty_label = '납부회차별 검색'
        self.fields['ba'].queryset = ProjectBankAccount.objects.filter(project=project)
        self.fields['ba'].empty_label = '납부계좌별 검색'


class PaymentForm(forms.ModelForm):
    class Meta:
        model = ProjectCashBook
        fields = ('project', 'project_account_d2', 'project_account_d3', 'contract',
                  'deal_date', 'installment_order', 'income', 'bank_account', 'trader', 'note')
        widgets = {
            'project': forms.HiddenInput(), 'contract': forms.HiddenInput(),
            'project_account_d2': forms.HiddenInput(), 'project_account_d3': forms.HiddenInput(),
        }

    def __init__(self, project, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        self.fields['installment_order'].queryset = InstallmentPaymentOrder.objects.filter(project=project)
        self.fields['installment_order'].empty_label = '납부회차선택'
        self.fields['bank_account'].queryset = ProjectBankAccount.objects.filter(project=project)
        self.fields['bank_account'].empty_label = '수납계좌선택'
