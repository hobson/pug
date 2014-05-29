# -*- coding: utf-8 -*-
from case.models import Case
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit #, Layout, Field, Div, HTML, Button, Row

from call_center.models import Refrefurb


class GetLagForm(forms.Form):

    model = forms.CharField(max_length=512, required=False,
        label='Model Numbers',
        initial='LC',
        help_text='comma-separated list of model numbers')

    lag_min = forms.IntegerField(max_value=365*10, min_value=-60, required=False,
        label='Minimum Lag (days)',
        initial=0,
        help_text='Minimum number of lag from sale to return in days to display')

    lag_max = forms.IntegerField(max_value=365*10, min_value=-60, required=False,
        label='Maximum Lag (days)',
        initial=365*3,
        help_text='Maximum number of lag from sale to return in days to display')

    fiscal_years = forms.MultipleChoiceField(
        label='Fiscal Years',
        initial='2013', required=False, 
        choices=tuple(('%d' % i, '%d' % i) for i in range(2009, 2014)),
        widget=forms.CheckboxSelectMultiple,
        help_text="fiscal years to compare",
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-GetLagForm'
        self.helper.help_text_inline = True
        # self.helper.form_class = 'blueForms'
        self.helper.form_method = 'GET'
        self.helper.form_action = ''

        self.helper.add_input(Submit('submit', 'Submit'))
        super(GetLagForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Refrefurb
        fields = ['model',]


class GetCasesForm(forms.Form):

    model = forms.CharField(required=False,
        max_length=2048,
        label='Model Numbers',
        initial='LC',
        help_text='comma-separated list of model numbers or model number prefixes',
        )

    serial = forms.CharField(required=False,
        max_length=2048,
        label='Serial Numbers',
        initial='',
        help_text='comma-separated list of serial numbers (one for each model_number, or blank for all appropriate serial_numbers)',
        )

    reason = forms.CharField(required=False,
        max_length=128,
        label='Return Reason Codes (r-codes)',
        initial='R',
        help_text='comma-separated list of reason codes or reason-code prefixes',
        )

    account= forms.CharField(required=False,
        max_length=256,
        label='Customer Account Numbers',
        initial='',
        help_text='comma-separated list of customer account numbers',
        )

    fiscal_years = forms.CharField(max_length=256, required=False,
        label='Fiscal Years',
        initial='13', 
        help_text="comma-separated list of fiscal years to compare",
        )

    lag_min = forms.IntegerField(max_value=365*3, min_value=-60, required=False,
        label='Minimum Lag (days)',
        initial=0,
        help_text='Minimum number of lag from sale to return in days to display',
        )

    lag_max = forms.IntegerField(max_value=365*3, min_value=-60, required=False,
        label='Maximum Lag (days)',
        initial=0,
        help_text='Maximum number of lag from sale to return in days to display')


    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-GetLagForm'
        self.helper.help_text_inline = True
        # self.helper.form_class = 'blueForms'
        self.helper.form_method = 'GET'
        self.helper.form_action = ''

        self.helper.add_input(Submit('submit', 'Submit'))
        super(GetCasesForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Refrefurb
        fields = ['model',]


class GetCaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-GetCaseForm'
        self.helper.help_text_inline = True
        # self.helper.form_class = 'blueForms'
        self.helper.form_method = 'POST'
        self.helper.form_action = '/timeline/'

        #self.helper.add_input(Submit('submit', 'Submit'))
        super(GetCaseForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Case
        fields = ['model_number', 'serial_number']
