# -*- coding: utf-8 -*-
import datetime

from django import forms
#from pug.nlp import util


class GetLagForm(forms.Form):

    mn = forms.CharField(max_length=512, required=False,
        label='Model Numbers',
        initial='',
        help_text='e.g. "LC40, LC5, LC60E79U"',
        #widget=forms.TextInput(attrs={'placeholder': 'LC60E79U, LC60LE835U, ...'}),
        )

    sg = forms.CharField(required=False,
        max_length=128,
        label='Product Department',
        initial='',
        help_text='e.g. "117, 118, 119"',
        )

    an= forms.CharField(required=False,
        max_length=256,
        label='Refurb Account',
        initial='',
        help_text="e.g. 113656, 100479, 105158",
        )

    exclude = forms.ChoiceField(
        initial='I',
        label='Exclude?',
        choices=(('I', 'Include'), ('E', 'Exclude')),
        # widget=forms.RadioSelect,
        )

    r = forms.CharField(required=False,
        max_length=128,
        label='R-Code',
        initial='',
        help_text='e.g. "R11, R12, R13"',
        )

    min_lag = forms.CharField(required=False,
        max_length=16,
        label='Min Lag',
        initial='',
        help_text='Minimum days between sale & return',
        )

    max_lag = forms.CharField(required=False,
        max_length=16,
        label='Max Lag',
        initial='',
        help_text='Maximum days between sale & return',
        )

    min_date = forms.DateField(
        required=False,
        label='Min Date',
        initial=datetime.date(2012, 4, 1),
        help_text='e.g. "2013-03-31"',
        )

    max_date = forms.DateField(
        required=False,
        label='Max Date',
        initial=datetime.date.today,
        help_text='e.g. "2014-04-01"',
        )

    fy = forms.CharField(max_length=256, required=False,
        label='Fiscal Years',
        initial='13', 
        help_text='e.g. 12, \'13, 2014',
        )

    ##### These fields aren't data filters, but aggregation configuration values

    regex = forms.CharField(max_length=256, required=False,
        label='Comments Search Pattern (<a href="https://www.icewarp.com/support/online_help/203030104.htm">regex</a>)',
        initial='MURA|HORIZ', 
        help_text='e.g. MURA|HORIZ',
        )

    columns = forms.CharField(max_length=256, required=False,
        label='CSV Columns (semicolon-separated)',
        initial='', 
        help_text='e.g. model; inspnote; recvnotes; repanote; ',
        )

    ##### These fields are for the dashboard functionality, recording and displaying aggregates that you want

    name = forms.CharField(max_length=128, required=False,
        label='Name or Description',
        initial='',
        help_text='e.g. BB-2014-LC70',
        )

    aggregate_ids = forms.CharField(max_length=128, required=False,
        label='ID numbers of previous queries to display', #  for display in a Dashboard (table or plot of aggregates)
        initial='',
        help_text='e.g. -3,-2,-1  or 98,99,100',
        widget=forms.HiddenInput(),
        )

    def __init__(self, *args, **kwargs):
        super(GetLagForm, self).__init__(*args, **kwargs)

    # def clean(self):
    #     if 'fast' in self.data:
    #         return self.cleaned_data.update({'submit': 'fast'})
    #         # return self.cleaned_data.update({'submit': 'fast'})
    #     elif 'zoomable' in self.data:
    #         return self.cleaned_data.update({'submit': 'zoomable'})
    #     return self.cleaned_data
            # do unsubscribe


