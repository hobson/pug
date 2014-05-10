# -*- coding: utf-8 -*-
from case.models import Case, InspectionEvent
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, Div, HTML, Button, Row

class GetLagForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-GetCaseForm'
        self.helper.help_text_inline = True
        # self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'
        self.helper.form_action = '/timeline/'

        self.helper.add_input(Submit('submit', 'Submit'))
        super(GetCaseForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Case
        fields = ['model_number', 'serial_number']
