# -*- coding: utf-8 -*-
import datetime

from case.models import Case
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit #, Layout, Field, Div, HTML, Button, Row


class GetLagForm(forms.Form):

    model = forms.CharField(max_length=512, required=False,
        label='Model Numbers',
        initial='',
        help_text='Comma-separated list of model numbers')

    serial = forms.CharField(required=False,
        max_length=2048,
        label='Serial Numbers',
        initial='',
        help_text='Comma-separated list of serial numbers (one for each Model Number, or blank)',
        )

    reason = forms.CharField(required=False,
        max_length=128,
        label='Return Reason Codes (r-codes)',
        initial='',
        help_text='Comma-separated list of reason codes or reason-code prefixes',
        )

    account= forms.CharField(required=False,
        max_length=256,
        label='Customer Account Numbers',
        initial='',
        help_text='Comma-separated list of customer account numbers',
        )

    min_lag = forms.IntegerField(max_value=365*10, min_value=-60, required=False,
        label='Minimum Lag (days)',
        initial=0,
        help_text='Minimum number of lag from sale to return in days')

    max_lag = forms.IntegerField(max_value=365*10, min_value=-60, required=False,
        label='Maximum Lag (days)',
        initial=365*3,
        help_text='Maximum number of lag from sale to return in days')

    min_date = forms.DateField(
        required=False,
        label='Minimum Return Date',
        initial=datetime.date(2012, 4, 1),
        help_text='Minimum return received date')

    max_date = forms.DateField(
        required=False,
        label='Maximum Return Date',
        initial=datetime.date.today,
        help_text='Maximum return received date')

    fiscal_years = forms.CharField(max_length=256, required=False,
        label='Fiscal Years',
        initial='13', 
        help_text="Comma-separated list of fiscal years",
        )

    def __init__(self, *args, **kwargs):
        print 'initial: %r' % kwargs.get('initial')
        self.helper = FormHelper()
        self.helper.form_id = 'id-GetLagForm'
        self.helper.help_text_inline = True
        # self.helper.form_class = 'blueForms'
        self.helper.form_method = 'GET'
        self.helper.form_action = ''

        self.helper.add_input(Submit('submit', 'Submit'))
        super(GetLagForm, self).__init__(*args, **kwargs)



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
