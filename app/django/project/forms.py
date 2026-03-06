from django import forms
from django.forms.models import modelformset_factory
from django.forms.widgets import TextInput

from contract.models import OrderGroup
from items.models import UnitType, UnitFloorType
from payment.models import SalesPriceByGT, InstallmentPaymentOrder, DownPayment
from .models import Project, Site, SiteOwner, SiteContract


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = ('company',)


OrderGroupFormSet = modelformset_factory(OrderGroup, exclude=('project',))


class UnitTypeForm(forms.ModelForm):  # admin.py use
    class Meta:
        model = UnitType
        fields = '__all__'
        widgets = {'color': TextInput(attrs={'type': 'color'})}


UnitTypeFormSet = modelformset_factory(UnitType,
                                       form=UnitTypeForm,
                                       exclude=('project',),
                                       extra=0)

UnitFloorTypeFormSet = modelformset_factory(UnitFloorType,
                                            exclude=('project',))

SalesPriceByGTFormSet = modelformset_factory(SalesPriceByGT,
                                             exclude=('project',),
                                             widgets={'order_group': forms.HiddenInput(),
                                                      'unit_type': forms.HiddenInput(),
                                                      'unit_floor_type': forms.HiddenInput()}, extra=0)

InstallmentPaymentOrderFormSet = modelformset_factory(InstallmentPaymentOrder,
                                                      exclude=('project',))

DownPaymentFormSet = modelformset_factory(DownPayment, exclude=('project',))


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = '__all__'
        widgets = {'project': forms.HiddenInput()}


class SiteOwnerForm(forms.ModelForm):
    class Meta:
        model = SiteOwner
        fields = '__all__'
        widgets = {'project': forms.HiddenInput(), 'user': forms.HiddenInput()}

    def __init__(self, project, *args, **kwargs):
        super(SiteOwnerForm, self).__init__(*args, **kwargs)
        self.fields['sites'].queryset = Site.objects.filter(project=project)


class SiteContractForm(forms.ModelForm):
    class Meta:
        model = SiteContract
        fields = '__all__'
        widgets = {'project': forms.HiddenInput(), 'user': forms.HiddenInput()}

    def __init__(self, project, *args, **kwargs):
        super(SiteContractForm, self).__init__(*args, **kwargs)
        self.fields['owner'].queryset = SiteOwner.objects.filter(project=project).order_by('id')
