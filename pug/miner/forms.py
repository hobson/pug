# -*- coding: utf-8 -*-
import datetime

from django import forms


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
        #widget=forms.TextInput(attrs={'placeholder': '117, 118, 119 ...'}),
        )

    an= forms.CharField(required=False,
        max_length=256,
        label='Refurb Account',
        initial='',
        help_text="e.g. 113656, 100479, 105158",
        #widget=forms.TextInput(attrs={'placeholder': "Comma-separated customer account #'s"}),
        )

    exclude = forms.ChoiceField(
        #widget=forms.RadioSelect,
        initial='I',
        label='Exclude?',
        choices=(('I', 'Include'), ('E', 'Exclude'))
        )

    r = forms.CharField(required=False,
        max_length=128,
        label='R-Code',
        initial='',
        help_text='e.g. "R11, R12, R13"',
        #widget=forms.TextInput(attrs={'placeholder': 'R10, R13, ...'}),
        )

    min_lag = forms.CharField(required=False,
        label='Min Lag',
        initial='',
        help_text='Min days between sale & return',
        #widget=forms.TextInput(attrs={'placeholder': 'Min days between sale & return'}),
        )

    max_lag = forms.CharField(required=False,
        label='Max Lag',
        initial='',
        help_text='Max days between sale & return',
        #widget=forms.TextInput(attrs={'placeholder': 'Max days between sale & return'}),
        )

    min_date = forms.DateField(
        required=False,
        label='Min Date',
        initial=datetime.date(2012, 4, 1),
        help_text='e.g. "2013-03-31"',
        #widget=forms.DateInput(), #attrs={'placeholder': 'e.g. 2014-04-01'}
        )

    max_date = forms.DateField(
        required=False,
        label='Max Date',
        initial=datetime.date.today,
        help_text='e.g. "2014-04-01"',
        #widget=forms.DateInput(), #attrs={'placeholder': 'e.g. 2014-04-01'}
        )

    fy = forms.CharField(max_length=256, required=False,
        label='Fiscal Years',
        initial='13', 
        help_text='e.g. 12, \'13, 2014',
        # widget=forms.TextInput(attrs={'placeholder': '12, 2013, 14, ...'}),
        )

    regex = forms.CharField(max_length=256, required=False,
        label='Comments Search Pattern (<a href="https://www.icewarp.com/support/online_help/203030104.htm">regex</a>)',
        initial='MURA|HORIZ', 
        help_text='e.g. MURA|HORIZ',
        # widget=forms.TextInput(attrs={'placeholder': '12, 2013, 14, ...'}),
        )

    columns = forms.CharField(max_length=256, required=False,
        label='CSV Columns (semicolon-separated)',
        initial='', 
        help_text='e.g. model; inspnote; recvnotes; repanote; ',
        # widget=forms.TextInput(attrs={'placeholder': '12, 2013, 14, ...'}),
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


