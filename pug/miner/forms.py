# -*- coding: utf-8 -*-
import datetime

from case.models import Case
from django import forms
from crispy_forms.helper import FormHelper
# from crispy_forms.layout import Submit #, Layout, Field, Div, HTML, Button, Row


class GetLagForm(forms.Form):

    mn = forms.CharField(max_length=512, required=False,
        label='Model Numbers',
        initial='',
        help_text='Comma-separated model numbers',
        widget=forms.TextInput(attrs={'placeholder': 'LC60E79U, LC60LE835U, ...'}),
        )

    sg = forms.CharField(required=False,
        max_length=128,
        label='Product Department',
        initial='',
        help_text='Product Department numbers (e.g. 117, 118, 119) associated with subsets of model numbers',
        widget=forms.TextInput(attrs={'placeholder': '117, 118, 119 ...'}),
        )

    # sn = forms.CharField(required=False,
    #     max_length=2048,
    #     label='Serial Numbers',
    #     initial='',
    #     help_text='Comma-separated serial numbers',
    #     widget=forms.TextInput(attrs={'placeholder': '205815430, 109840374, ...'}),
    #     )

    an= forms.CharField(required=False,
        max_length=256,
        label='Refurb Account',
        initial='',
        help_text="Comma-separated customer account #'s",
        widget=forms.TextInput(attrs={'placeholder': "Comma-separated customer account #'s"}),
        )

    r = forms.CharField(required=False,
        max_length=128,
        label='R-Code',
        initial='',
        help_text='Comma-separated reason codes',
        widget=forms.TextInput(attrs={'placeholder': 'R10, R13, ...'}),
        )

    min_lag = forms.IntegerField(max_value=365*10, min_value=-60, required=False,
        label='Min Lag',
        initial=0,
        help_text='Min days between sale & return',
        widget=forms.TextInput(attrs={'placeholder': 'Min days between sale & return'}),
        )

    max_lag = forms.IntegerField(max_value=365*10, min_value=-60, required=False,
        label='Max Lag',
        initial=365*3,
        help_text='Max days between sale & return',
        widget=forms.TextInput(attrs={'placeholder': 'Max days between sale & return'}),
        )

    min_date = forms.DateField(
        required=False,
        label='Min Date',
        initial=datetime.date(2012, 4, 1),
        help_text='Minimum return received date',
        widget=forms.DateInput(), #attrs={'placeholder': 'e.g. 2014-04-01'}
        )

    max_date = forms.DateField(
        required=False,
        label='Max Date',
        initial=datetime.date.today,
        help_text='Maximum return received date',
        widget=forms.DateInput(), #attrs={'placeholder': 'e.g. 2014-04-01'}
        )

    fy = forms.CharField(max_length=256, required=False,
        label='Fiscal Years',
        initial='13', 
        help_text="Comma-separated list of fiscal years",
        widget=forms.TextInput(attrs={'placeholder': '12, 2013, 14, ...'}),
        )

    def __init__(self, *args, **kwargs):
        # self.helper = FormHelper()
        # # self.helper.form_class = 'form-horizontal'  # 'form-inline', 'blueForms'
        # # self.helper.form_id = 'id-GetLagForm'
        # # self.helper.help_text_inline = True

        # self.helper.form_method = 'GET'
        # self.helper.form_action = ''  # url that is triggered, carrying a GET or POST payload

        # self.helper.add_input(Submit('fast', 'Quick Table'))
        # self.helper.add_input(Submit('detail', 'Detailed Table'))
        # self.helper.add_input(Submit('zoomable', 'Zoomable Plot'))
        # self.helper.add_input(Submit('linked', 'Linked Plot'))
        super(GetLagForm, self).__init__(*args, **kwargs)

    # def clean(self):
    #     if 'fast' in self.data:
    #         return self.cleaned_data.update({'submit': 'fast'})
    #         # return self.cleaned_data.update({'submit': 'fast'})
    #     elif 'zoomable' in self.data:
    #         return self.cleaned_data.update({'submit': 'zoomable'})
    #     return self.cleaned_data
            # do unsubscribe


class GetCaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-GetCaseForm'
        self.helper.help_text_inline = False
        # self.helper.form_class = 'blueForms'
        self.helper.form_method = 'POST'
        self.helper.form_action = '/timeline/'

        #self.helper.add_input(Submit('submit', 'Submit'))
        super(GetCaseForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Case
        fields = ['model_number', 'serial_number']
