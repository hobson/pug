# -*- coding: utf-8 -*-
import os
import csv
import datetime
import math
import collections
import re
import string
import json

import pandas as pd

from django.shortcuts import render_to_response
from django.views.generic import View, TemplateView
from django.template import RequestContext
from django.template.response import TemplateResponse #, HttpResponse
from django.template.loader import get_template
from django.http import Http404, HttpResponse
from django import http

# from django.shortcuts import render
# from django.conf import settings

from pug.nlp import parse
from pug.nlp import util
from pug.nlp import db

# from sec_sharp_refurb.models import Refrefurb as SECRef
#import call_center.models as SLAmodels
from forms import GetLagForm

# format options for lag histograms:
#   hist = ff = fd = Frequency Distribution/Function (histogram of counts)
#   pmf = pdf = Probability Mass/Distribution Function (or PDF, probability distribution/density function)
#   cmf = cdf = Cumulative Distribution/Mass Function (cumulative probability)
#   cfd = cff = Cumulative Frequency Distribution/Function (cumulative counts)


def explorer(request, graph_uri=None):
    """Explore the database (or any data provided by a REST service)"""
    #return HttpResponse('Looking for template in miner/explorer.html')
    return render_to_response('miner/explorer.html')


def home(request):
    """Explore the database (or any data provided by a REST service)"""
    return render_to_response('miner/home.html')


def connections(request, edges):
    """
    Plot a force-directed graph based on the edges provided
    """
    edge_list, node_list = parse.graph_definition(edges)
    data = {'nodes': json.dumps(node_list), 'edges': json.dumps(edge_list)}
    return render_to_response('miner/connections.html', data)


def stats(request, date_offset=0, fields=None, title_prefix=None, model='WikiItem'):
    """
    In addition to chart data in data['chart'], send statistics data to view in data['stats']
    """
    data = {}

    modified_chart_data = data['chart']['chartdata']
    if 'y2' in data['chart']['chartdata']:
        matrix = db.Columns([modified_chart_data['y1'], modified_chart_data['y2']], ddof=0, tall=True)
    else:
        fields = ['date/time'] + fields
        matrix = db.Columns([modified_chart_data['x'], modified_chart_data['y']], ddof=0, tall=True)
    if fields and len(fields) > 1:
        fields = fields[:2]
    else:
        fields = [
            data['chart']['chartdata'].get('name1') or 'time',
            data['chart']['chartdata'].get('name2') or data['chart']['chartdata'].get('name') or 'value',
            ]
    fields = util.pluralize_field_names(fields)
    data.update({
        'stats': {
            'fields': fields,
            'heading': 'Statistics',
            'cov': zip(fields, matrix.cov()),
            'R': zip(fields, matrix.rho),
            },
        })
    data['chart']['chartdata'] = modified_chart_data
    data['chart']['chart_title'] = 'Time Series'
    return render_to_response('miner/stats.html', data)


class StaticView(View):
    def get(self, request, *args, **kwargs):
        template_name = ''
        try:
            template_name += 'miner/staticview/' + kwargs.get('page', 'index.html')
            get_template(template_name) 
        except:
            try:
                template_name += 'miner/staticview/' + kwargs.get('page', '') + '.html'
                get_template(template_name)
            except:
                raise Http404()
        return TemplateResponse(request, template_name)


class JSONView(View):
    def get(self, request, *args, **kwargs):
        # print os.path.join('static', kwargs.get('page', '') + '.json')
        # print os.path.realpath(os.path.curdir)
        # print os.getcwd()
        # print os.path.dirname(os.path.realpath(os.path.curdir))
        try:
            path = os.path.join('static', kwargs.get('page', '') + '.json')
            context = json.load(path)
        except:
            raise Http404()
        return self.render_to_response(context)

    def render_to_response(self, context, indent=None):
        "Returns a JSON response containing 'context' as payload"
        return self.get_json_response(self.convert_context_to_json(context, indent=indent))

    def get_json_response(self, content, **httpresponse_kwargs):
        "Construct an `HttpResponse` object."
        return http.HttpResponse(content,
                                 content_type='application/json',
                                 **httpresponse_kwargs)

    def convert_context_to_json(self, context, indent=None):
        "Convert the context dictionary into a JSON object"
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.
        return json.dumps(context, indent=indent)


# FIXME: move this back to sharp repo/apps
def context_from_request(request, context=None, Form=GetLagForm, delim=',', verbosity=0, **kwargs):
    """Process GET query request to normalize query arguments (split lists, etc)

    TODO: Generalize this for any list of API variables/strings and separators for lists

    Returns context dict with these updated elements:
    context['form']                a Form object populated with the normalized form field values from the GET query
    context['form_is_valid']       True  or False
    context['errors']              list of validation error messages to be displayed at top of form
    context['plot']                normalized acronym for one of 4 histogram type: 'hist', 'pmf', 'cmf', or 'cfd'
    contexxt['plot_name']          descriptive name for the plot type: 'Histogram', 'Probability Mass Function' ...
    context['table']               'fast' or 'detailed'
    context['limit']               int indicating the maximum number of rows (for speeding the query for a detailed table)
    context['regex']               regular expression string to test whether inspection notes and comments match
    context['columns']             columns to display in quicktable and csv
    context['filter']              dict for use in a Django queryset filter:
    {
        'model_numbers': mn.split(',')  #    list of strings for ?mn=
        'sales_groups': sg.split(',')  #     list of strings for ?sg=
        'fiscal_years': sn.split(',')  #     list of strings for ?fy=
        'reasons': sn.split(',')  #          list of strings for ?r=
        'account_numbers': an.split(',')  #  list of strings for ?an=
        'min_dates': sn.split(',')  #        list of strings for ?min_date=
        'max_dates': sn.split(',')  #        list of strings for ?max_date=
        'min_lag': sn.split(',')  #          list of strings for ?min_lag=
        'max_lag': sn.split(',')  #          list of strings for ?max_lag=
        'exclude': sn.split(',')  #          "E" or "I" (include or exclude account numbers)
        'columns': columns.split(';')  #          list of fields for columns of CSV
    }
    """
    context = context or RequestContext(request)

    context['errors'] = []
    context['filter'] = {}

    limit = request.GET.get('limit') or request.GET.get('num') or request.GET.get('num_rows') or request.GET.get('rows') or request.GET.get('records') or request.GET.get('count', 0)

    context['plot'] = (request.GET.get('plot', '') or request.GET.get('plt', '') or request.GET.get('p', '') 
                        or request.GET.get('chart', '') or request.GET.get('chrt', '')
                        ).strip().lower()
    context['plot'] = util.HIST_NAME.get(context['plot'][-3:], context['plot'])
    context['plot_name'] = util.HIST_CONFIG[context['plot']]['name'] if context['plot'] else ''


    context['table'] = (request.GET.get('table', '') or request.GET.get('tbl', '') or request.GET.get('tble', '') 
                        or request.GET.get('tab', '') or request.GET.get('t', '')
                        ).strip().lower()
    if context['table'].startswith('f'):
        context['table'] = 'fast'
    if context['table'].startswith('a'):
        context['table'] = 'aggregate'
        context['aggregates'] = []
        # context['plot'] = 'aggregate'
    if context['table'].startswith('d'):
        context['table'] = 'detailed'
        limit = limit or 10*1000
    context['limit'] = util.make_int(limit)

    mn = request.GET.get('mn', "") or request.GET.get('model', "") or request.GET.get('models', "") or request.GET.get('model_number', "") or request.GET.get('model_numbers', "")
    mn = [s.strip().upper() for s in mn.split(',')] or ['']
    context['filter']['model_numbers'] = mn

    sg = request.GET.get('sg', "") or request.GET.get('group', "") or request.GET.get('sales', "") or request.GET.get('sales_group', "") or request.GET.get('sale_group_number', "")
    sg = [s.strip().upper() for s in sg.split(',')] or ['']
    # need to implement filters on sales_group (where serial_numbers was, in explore_lags, and filter_sla_lags or lags_dict)
    context['filter']['sales_groups'] = sg

    fy = request.GET.get('fy', "") or request.GET.get('yr', "") or request.GET.get('year', "") or request.GET.get('years', "") or request.GET.get('fiscal_year', "") or request.GET.get('fiscal_years', "")
    fiscal_years = [util.normalize_year(y) for y in fy.split(',')] or []
    fiscal_years = [str(y) for y in fiscal_years if y]
    context['filter']['fiscal_years'] = fiscal_years

    rc = request.GET.get('r', "") or request.GET.get('rc', "") or request.GET.get('rcode', "") or request.GET.get('reason', "") or request.GET.get('reasons', "")
    context['filter']['reasons'] = [s.strip().upper() for s in rc.split(',')] or ['']

    an = request.GET.get('a', "") or request.GET.get('an', "") or request.GET.get('account', "") or request.GET.get('account_number', "") or request.GET.get('account_numbers', "")
    context['filter']['account_numbers'] = [s.strip().upper() for s in an.split(',')] or []

    exclude = request.GET.get('exclude', "") or request.GET.get('e', "") or request.GET.get('x', "") or request.GET.get('ex', "") or request.GET.get('excl', "I")
    context['exclude'] = 'E' if exclude.upper().startswith('E') else ''

    min_dates = request.GET.get('mind') or request.GET.get('min_date') or request.GET.get('min_dates') or ""
    min_dates = [s.strip() for s in min_dates.split(',')] or ['']
    context['filter']['min_dates'] = min_dates

    max_dates = request.GET.get('maxd') or request.GET.get('max_date') or request.GET.get('max_dates') or ""
    max_dates = [s.strip() for s in max_dates.split(',')] or ['']
    context['filter']['max_dates'] = max_dates

    context['regex'] = request.GET.get('re') or request.GET.get('regex') or request.GET.get('word') or request.GET.get('search') or request.GET.get('find') or ""

    context['columns'] = request.GET.get('col') or request.GET.get('cols') or request.GET.get('column') or request.GET.get('columns') or ""
    context['columns'] = [s.strip() for s in context['columns'].split(';')] or []

    context['aggregate_ids'] = request.GET.get('agg') or request.GET.get('ids') or request.GET.get('aggids') or request.GET.get('aggregates') or request.GET.get('aggregate_ids') or '-1'
    context['aggregate_ids'] = [int(s.strip()) for s in context['aggregate_ids'].split(',') if s and s.strip()] or [-1]

    # whether the FK join queries should be short-circuited
    print 'aggregate_ids: ', context['aggregate_ids']
    context['quick'] = context.get('quick') or (context['table'].startswith('agg') and context['aggregate_ids'] and not (context['aggregate_ids'][-1] == -1) and not context['table'] == 'fast')
    print context['quick']

    # lag values can't be used directly in a django filter so don't put them in context['filter']
    lag = request.GET.get('lag', '') or request.GET.get('l', '')
    lag = [s.strip().upper() for s in lag.split(',')] or ['']
    maxl = request.GET.get('max_lag', '') or request.GET.get('maxlag', '') or request.GET.get('maxl', '')
    minl = request.GET.get('min_lag', '') or request.GET.get('minlag', '') or request.GET.get('maxl', '')

    try:
        lag = int(lag)
        minl = lag - 7
        maxl = lag
    except:
        try:
            minl = int(minl)
        except:
            minl = ''
        try:
            maxl = int(maxl)
        except:
            maxl = ''

    context['filter']['min_lag'] = minl
    context['filter']['max_lag'] = maxl

    initial = {
                'mn':       ', '.join(m.strip() for m in context['filter']['model_numbers'] if m.strip()), 
                'sg':       ', '.join(context['filter']['sales_groups']),
                'r':        ', '.join(context['filter']['reasons']),
                'an':       ', '.join(context['filter']['account_numbers']),
                'fy':       ', '.join(context['filter']['fiscal_years']),
                'exclude':            context['exclude'],
                'min_lag':            context['filter']['min_lag'],
                'max_lag':            context['filter']['max_lag'],
                'min_date': ', '.join(context['filter']['min_dates']),
                'max_date': ', '.join(context['filter']['max_dates']),
                'columns':  '; '.join(context['columns']),
                'regex':              context['regex'],
                'name':        ''
              }

    context['name'] = request.GET.get('s') or request.GET.get('n') or request.GET.get('series') or request.GET.get('name') or util.slug_from_dict(initial)

    if verbosity:
        print 'initial: {0}'.format(initial)
        print 'normalized GET query parameters: %r' % initial
        print 'Form before validation {0}'.format(Form)

    if request.method == 'POST':
        # GetLagForm only has a GET button
        context['form'] = Form(request.POST)
    elif request.method == 'GET':
        context['form'] = Form(data=initial, initial=initial)
    print Form

    context['form_is_valid'] = context['form'].is_valid()
    if not context['form_is_valid']:
        context['form_errors'] = context['form'].errors
        if verbosity:
            print 'ERRORS in FORM !!!!!!!!!!!!!'
            print context['form_errors']
        #import ipdb
        #ipdb.set_trace()
        #raise RuntimeError('form is invalid')

    if not context.get('field_names'):
        context['field_names'] = kwargs.get('field_names', [])

        
    if not context.get('filename'):
        context['filename'] = 'Refurb.csv'

    return context


def d3_plot_context(context, table=((0, 0),), title='Line Chart', xlabel='Time', ylabel='Value', header=None):
    """

    Arguments:
      table (list of lists of values): A CSV/Excel style table with an optional header row as the first list
      title (str): String to display atop the plot
      xlabel (str): Text to display along the bottom axis
      ylabel (str): Text to display along the vertical axis
    """
    if isinstance(table, pd.Series):
        table = pd.DataFrame(table, columns=header or [ylabel])
    if isinstance(table, pd.DataFrame):
        df = table.sort()
        table = list(table.sort().to_records())
        for i, row in enumerate(table):
            d = row[0]
            if isinstance(d, datetime.date):
                table[i][0] = "{1}/{2}/{0}".format(d.year, d.month, d.day)
        first_row = ['Date'] + list(str(c).strip() for c in df.columns)
        header = None
    else:
        first_row = list(table[0])
    N, M = len(table), max(len(row) for row in table)
    identifiers = header
    descriptions = header
    if not header and not all(isinstance(col, basestring) and col.strip() for col in first_row):
        print first_row
        if isinstance(header, bool):
            header = []
        else:
            header = [('y{0}'.format(i-1) if i else 'x') for i in range(M)]
    else:
        header = first_row
        table = table[1:]

    print header
    # header should now be a list of one list of strings or an empty list,
    # So now just need to make sure the names of the columns are valid javascript identifiers
    if header:
        identifiers = [util.make_name(h, language='javascript', space='') for h in header]
        table = [header] + table
        descriptions = [unicode(h) for h in header]

    print identifiers
    context['data'] = context.get('data', {})
    context['data'].update({
        #'lags_dict': {hist_type: lags},
        'title': title,
        'header': json.dumps(identifiers),
        'descriptions': json.dumps(descriptions),
        'xlabel': xlabel,
        'ylabel': ylabel,
        'd3data': json.dumps(util.transposed_lists(table)), 
        'form': {},
    })
    print context['data']
    return context
    # print context['data']


re_model_instance_dot = re.compile('__|[.]+')


def follow_double_underscores(obj, field_name=None, excel_dialect=True, eval_python=False, index_error_value=None):
    '''Like getattr(obj, field_name) only follows model relationships through "__" or "." as link separators

    >>> from django.contrib.auth.models import Permission
    >>> import math
    >>> p = Permission.objects.all()[0]
    >>> follow_double_underscores(p, 'content_type__name') == p.content_type.name
    True
    >>> follow_double_underscores(p, 'math.sqrt(len(obj.content_type.name))', eval_python=True) == math.sqrt(len(p.content_type.name))
    True
    '''
    if not obj:
        return obj
    if isinstance(field_name, list):
        split_fields = field_name
    else:
        split_fields = re_model_instance_dot.split(field_name)
    if False and eval_python:
        try:
            return eval(field_name, {'datetime': datetime, 'math': math, 'collections': collections}, {'obj': obj})
        except IndexError:
            return index_error_value
        except:
            pass

    if len(split_fields) <= 1:
        if hasattr(obj, split_fields[0]):
            value = getattr(obj, split_fields[0])
        elif hasattr(obj, split_fields[0] + '_id'):
            value = getattr(obj, split_fields[0] + '_id')
        elif hasattr(obj, split_fields[0] + '_set'):
            value = getattr(obj, split_fields[0] + '_set')
        elif split_fields[0] in obj.__dict__:
            value = obj.__dict__.get(split_fields[0])
        elif eval_python:
			value = eval('obj.' + split_fields[0])
        else:
            return follow_double_underscores(getattr(obj, split_fields[0]), field_name=split_fields[1:], eval_python=eval_python, index_error_value=index_error_value)
        if value and excel_dialect and isinstance(value, datetime.datetime):
            value = value.strftime('%Y-%m-%d %H:%M:%S')
        return value
    return follow_double_underscores(getattr(obj, split_fields[0]), field_name=split_fields[1:], eval_python=eval_python, index_error_value=index_error_value)


def table_generator_from_list_of_instances(data, field_names=None, excluded_field_names=None, sort=True, excel_dialect=True, eval_python=False):
    '''Return an iterator over the model instances (or queryset) that yeilds lists of values

    This forms a table suitable for output as a csv

    FIXME: allow specification of related field values with double_underscore

    >>> from django.contrib.auth.models import Permission
    >>> from django.db.models.base import ModelState
    >>> t = table_generator_from_list_of_instances(list(Permission.objects.all()))
    >>> import types
    >>> isinstance(t, types.GeneratorType)
    True
    >>> t = list(t)
    >>> len(t) > 3
    True
    >>> len(t[0])
    5
    >>> isinstance(t[0][0], basestring)
    True
    >>> isinstance(t[0][-1], basestring)
    True
    >>> isinstance(t[1][0], int)
    True
    >>> isinstance(t[0][2], basestring)
    True
    >>> isinstance(t[1][2], ModelState)
    True
    >>> isinstance(t[-1][2], ModelState)
    True
    '''
    excluded_field_names = excluded_field_names or []
    excluded_field_names += '_state'
    excluded_field_names = set(excluded_field_names)

    for i, row in enumerate(data):
        if not field_names or not any(field_names):
            field_names = [k for (k, v) in row.__dict__.iteritems() if not k in excluded_field_names]
        if not i:
            yield field_names
        yield [follow_double_underscores(row, field_name=k, excel_dialect=True, eval_python=eval_python) for k in field_names]


class DashboardView(TemplateView):
    """Query the miner.AggregateResults table to retrieve values for plotting in a bar chart"""
    template_name = 'miner/dashboard.d3.html'

    def get(self, request, *args, **kwargs):
        context = context_from_request(request)
        context = self.get_context_data(context)
        return self.render_to_response(context)

    def get_context_data(self, context, **kwargs):
        # Call the base implementation first to get a context
        context = super(DashboardView, self).get_context_data(**kwargs)
        return d3_plot_context(context, 
            table= util.transposed_lists([["x index"] + [907,901,855,902,903,904,905,906,900],["y value (units)", 99,51,72,43,54,65,76,67,98],["z-value (units)", 1,91,62,73,64,65,76,67,98],["abc's", 10,20,30,40,50,60,70,80,90]]),
            title='Line Chart', xlabel='ID Number', ylabel='Value', 
            header=None)


class BarPlotView(DashboardView):
    template_name = 'miner/bar_plot.d3.html'


class LinePlotView(DashboardView):
    template_name = 'miner/line_plot.d3.html'


class BlockView(DashboardView):
    """Query the miner.AggregateResults table to retrieve values for plotting in a bar chart"""
    template_name = 'miner/block.d3.html'


def csv_response_from_context(context=None, filename=None, field_names=None, null_string='', eval_python=True):
    """Generate the response for a Download CSV button from data within the context dict

    The CSV data must be in one of these places/formats:

    * context as a list of lists of python values (strings for headers in first list)
    * context['data']['d3data'] as a string in json format (python) for a list of lists of repr(python_value)s
    * context['data']['cases'] as a list of lists of python values (strings for headers in first list)
    * context['data']['cases'] as a django queryset or iterable of model instances (list, tuple, generator)

    If the input data is a list of lists (table) that has more columns that rows it will be trasposed before being processed
    """
    filename = filename or context.get('filename') or 'table_download.csv'
    field_names = field_names or context.get('field_names', [])
    # FIXME: too slow!
    if field_names and all(field_names) and all(all(c in (string.letters + string.digits + '_.') for c in s) for s in field_names):
        eval_python=False

    data = context

    # find the data table within the context dict. should be named 'data.cases' or 'data.d3data'
    if not (isinstance(data, (tuple, list)) and isinstance(data[0], (tuple, list))):
        data = json.loads(data.get('data', {}).get('d3data', '[[]]'))
        if not data or not any(data):
            data = context.get('data', {}).get('cases', [[]])

    if not isinstance(data, (list, tuple)) or not isinstance(data[0], (list, tuple)):
        data = table_generator_from_list_of_instances(data, field_names=field_names, eval_python=eval_python)

    try:
        if len(data) < len(data[0]):
            data = util.transposed_lists(data)  # list(list(row) for row in data)
    except TypeError:
        # no need to transpose if a generator was provided instead of a list or tuple (anything with a len attribute)
        pass

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    writer = csv.writer(response)
    for row in data:
        writer.writerow([unicode(s if not s == None else null_string).encode('UTF-8') for s in row])

    return response

