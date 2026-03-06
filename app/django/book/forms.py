from django import forms

from .models import Subject, Image


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ('title', 'level', 'content')


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('image',)


ImageFormSet = forms.models.inlineformset_factory(Subject, Image, form=ImageForm, extra=1)
