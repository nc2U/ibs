from django import forms

from .models import ContractorRelease


class ContractRegisterForm(forms.Form):
    project = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'project'}))
    task = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'task'}))
    order_group = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'order_group'}))
    type = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'type'}))
    key_unit = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'key_unit'}))
    house_unit = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'house_unit'}), required=False)
    back_url = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'back_url'}), required=False)

    # Contractor Model
    name = forms.CharField(max_length=10, label='계약자명')
    birth_date = forms.DateField(label='생년월일', required=False)
    GENDER_CHOICES = (('M', '남자'), ('F', '여자'))
    gender = forms.ChoiceField(widget=forms.RadioSelect, label='성별', choices=GENDER_CHOICES, required=False)
    REG_CHOICES = (('1', '미인가'), ('2', '인가'), ('3', '부적격'))
    qualification = forms.ChoiceField(label='등록상태', choices=REG_CHOICES, required=False)
    reservation_date = forms.DateField(label='청약일자', required=False)
    contract_date = forms.DateField(label='계약일자', required=False)
    note = forms.CharField(widget=forms.Textarea, required=False, label='비고')
    # ContractorAddress Model
    id_zipcode = forms.CharField(max_length=5, label='우편번호', required=False)
    id_address1 = forms.CharField(max_length=50, label='주민등록 주소', required=False)
    id_address2 = forms.CharField(max_length=30, label='상세주소', required=False)
    id_address3 = forms.CharField(max_length=30, label='참고항목', required=False)
    dm_zipcode = forms.CharField(max_length=5, label='우편번호', required=False)
    dm_address1 = forms.CharField(max_length=50, label='우편송부 주소', required=False)
    dm_address2 = forms.CharField(max_length=30, label='상세주소', required=False)
    dm_address3 = forms.CharField(max_length=30, label='참고항목', required=False)
    # ContractorContact Model
    cell_phone = forms.CharField(max_length=13, label='휴대전화')
    home_phone = forms.CharField(max_length=13, required=False, label='집 전화')
    other_phone = forms.CharField(max_length=13, required=False, label='기타 전화')
    email = forms.EmailField(required=False, label='이메일')


class ContractorReleaseForm(forms.ModelForm):
    class Meta:
        model = ContractorRelease
        fields = '__all__'
        widgets = {
            'project': forms.HiddenInput(), 'contractor': forms.HiddenInput(),
            'status': forms.HiddenInput(), 'user': forms.HiddenInput()
        }
