from django import forms

from payment.models import InstallmentPaymentOrder


class SalesBillIssueForm(forms.Form):
    # project = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'project'}))
    published_date = forms.DateField(label='발행일자')
    now_payment_order = forms.ModelChoiceField(queryset=InstallmentPaymentOrder.objects.all(), label='발행회차')
    now_due_date = forms.DateField(label='당회 납부기한', required=False)
    host_name = forms.CharField(max_length=20, label='시행자명')
    host_tel = forms.CharField(max_length=13, label='시행자 전화')
    agency = forms.CharField(max_length=20, label='대행사명', required=False)
    agency_tel = forms.CharField(max_length=13, label='대행사 전화', required=False)
    bank_account1 = forms.CharField(max_length=20, label='수납은행[1]')
    bank_number1 = forms.CharField(max_length=20, label='계좌번호[1]')
    bank_host1 = forms.CharField(max_length=15, label='예금주[1]')
    bank_account2 = forms.CharField(max_length=20, label='수납은행[2]', required=False)
    bank_number2 = forms.CharField(max_length=20, label='계좌번호[2]', required=False)
    bank_host2 = forms.CharField(max_length=15, label='예금주[2]', required=False)
    zipcode = forms.CharField(max_length=5, label='우편번호')
    address1 = forms.CharField(max_length=50, label='주소')
    address2 = forms.CharField(max_length=30, label='상세주소', required=False)
    address3 = forms.CharField(max_length=30, label='참고항목', required=False)
    title = forms.CharField(max_length=255, label='고지서 제목')
    content = forms.CharField(widget=forms.Textarea, label='고지서 내용')

    def __init__(self, project, *args, **kwargs):
        super(SalesBillIssueForm, self).__init__(*args, **kwargs)
        self.fields['now_payment_order'].queryset = InstallmentPaymentOrder.objects.filter(project=project)
