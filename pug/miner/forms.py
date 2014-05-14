# -*- coding: utf-8 -*-
from case.models import Case
from django import forms
from crispy_forms.helper import FormHelper
#from crispy_forms.layout import Submit #, Layout, Field, Div, HTML, Button, Row

from call_center.models import Refrefurb


class GetLagForm(forms.Form):

    model = forms.CharField(max_length=512, required=False,
        initial='LC6',
        help_text='Comma-separated list of model numbers or model-number prefixes, e.g. "LC6, LC5"')

    fiscal_years = forms.MultipleChoiceField(
        initial='2013', required=False, 
        choices=tuple(('%d' % i, '%d' % i) for i in range(2009, 2014)),
        widget=forms.CheckboxSelectMultiple,
        help_text="Fiscal years to compare in a single plot.",
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-GetLagForm'
        self.helper.help_text_inline = True
        # self.helper.form_class = 'blueForms'
        self.helper.form_method = 'GET'
        self.helper.form_action = '/miner/lag/'

        #self.helper.add_input(Submit('submit', 'Submit'))
        super(GetLagForm, self).__init__(*args, **kwargs)

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
