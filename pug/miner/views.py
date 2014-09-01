# -*- coding: utf-8 -*-
import os
import csv
import datetime

from django.shortcuts import render_to_response
from django.views.generic import View  #, TemplateView
from django.template import RequestContext
from django.template.response import TemplateResponse #, HttpResponse
from django.template.loader import get_template
from django.http import Http404, HttpResponse
from django import http
from django.utils import simplejson as json
# from django.shortcuts import render

from pug.nlp import parse
from pug.nlp import util
from pug.nlp import db

# from sec_sharp_refurb.models import Refrefurb as SECRef
import call_center.models as SLAmodels
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

    def render_to_response(self, context):
        "Returns a JSON response containing 'context' as payload"
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        "Construct an `HttpResponse` object."
        return http.HttpResponse(content,
                                 content_type='application/json',
                                 **httpresponse_kwargs)

    def convert_context_to_json(self, context):
        "Convert the context dictionary into a JSON object"
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.
        return json.dumps(context)

   
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
    context['filter']              dict for use in a Django queryset filter:
    {
        'model_numbers': mn.split(',')  #    list of strings for ?mn=
        'sales_groups': sg.split(',')  #     list of strings for ?sg=
        'fiscal_years': sn.split(',')  #     list of strings for ?fy=
        'reasons': sn.split(',')  #          list of strings for ?r=
        'account_numbers': sn.split(',')  #  list of strings for ?an=
        'min_dates': sn.split(',')  #        list of strings for ?min_date=
        'max_dates': sn.split(',')  #        list of strings for ?max_date=
        'min_lag': sn.split(',')  #          list of strings for ?min_lag=
        'max_lag': sn.split(',')  #          list of strings for ?max_lag=
        'exclude': sn.split(',')  #          "E" or "I" (include or exclude account numbers)
    }
    """
    context = context or RequestContext(request)

    context['errors'] = []
    context['filter'] = {}

    limit = request.GET.get('limit', 0) or request.GET.get('num', 0) or request.GET.get('num_rows', 0) or request.GET.get('rows', 0) or request.GET.get('records', 0) or request.GET.get('count', 0)

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
    #context['filter']['sales_groups'] = sg
    context['filter']['sales_groups'] = sg

    #context['filter']['model_numbers'] += SLAmodels.models_from_sales_groups(context['sales_groups'])

    fy = request.GET.get('fy', "") or request.GET.get('yr', "") or request.GET.get('year', "") or request.GET.get('years', "") or request.GET.get('fiscal_year', "") or request.GET.get('fiscal_years', "")
    fiscal_years = [util.normalize_year(y) for y in fy.split(',')] or []
    fiscal_years = [str(y) for y in fiscal_years if y]
    context['filter']['fiscal_years'] = fiscal_years

    r = request.GET.get('r', "") or request.GET.get('rc', "") or request.GET.get('rcode', "") or request.GET.get('reason', "") or request.GET.get('reasons', "")
    r = [s.strip().upper() for s in r.split(',')] or ['']
    context['filter']['reasons'] = r

    a = request.GET.get('a', "") or request.GET.get('an', "") or request.GET.get('account', "") or request.GET.get('account_number', "") or request.GET.get('account_numbers', "")
    a = [s.strip().upper() for s in a.split(',')] or ['']
    context['filter']['account_numbers'] = a

    exclude = request.GET.get('exclude', "") or request.GET.get('e', "") or request.GET.get('x', "") or request.GET.get('ex', "") or request.GET.get('excl', "I")
    context['exclude'] = 'E' if exclude.upper().startswith('E') else 'I'

    min_dates = request.GET.get('mind', "") or request.GET.get('min_date', "") or request.GET.get('min_dates', "")
    min_dates = [s.strip() for s in min_dates.split(',')] or ['']
    context['filter']['min_dates'] = min_dates

    max_dates = request.GET.get('maxd', "") or request.GET.get('max_date', "") or request.GET.get('max_dates', "")
    max_dates = [s.strip() for s in max_dates.split(',')] or ['']
    context['filter']['max_dates'] = max_dates

    context['regex'] = request.GET.get('re', "") or request.GET.get('regex', "") or request.GET.get('word', "") or request.GET.get('search', "") or request.GET.get('find', "")

    series_name = request.GET.get('s', "") or request.GET.get('n', "") or request.GET.get('series', "") or request.GET.get('name', "")
    filter_values = series_name.split(' ')  # FIXME: '|'
    if filter_values and len(filter_values)==4:
        mn = [filter_values[0].strip('*')]
        context['filter']['model_numbers'] = mn  # SLAmodels.models_from_sales_groups(mn)
        r = [filter_values[1].strip('*')]
        context['filter']['reasons'] = r
        a = [filter_values[2].strip('*')]
        context['filter']['account_numbers'] = a
        fiscal_years = [filter_values[3].strip('*')]
        context['filter']['fiscal_years'] = fiscal_years

    lag_days = request.GET.get('lag', None)
    max_lag = request.GET.get('max_lag', None)
    min_lag = request.GET.get('min_lag', None)
    try:
        min_lag = int(lag_days) - 7
        max_lag = int(lag_days)
    except:
        min_lag = int(min_lag or 0)
        max_lag = int(max_lag or 180)
    
    initial = {
                'mn': ', '.join(m.strip() for m in context['filter']['model_numbers'] if m.strip()), 
                'sg': ', '.join(context['filter']['sales_groups']),
                'r': ', '.join(context['filter']['reasons']),
                'an': ', '.join(context['filter']['account_numbers']),
                'fy': ', '.join(context['filter']['fiscal_years']),
                'exclude': str(exclude),
                'min_lag': str(min_lag),
                'max_lag': str(max_lag),
                'min_date': ', '.join(context['filter']['min_dates']),
                'max_date': ', '.join(context['filter']['max_dates']),
                'regex': ', '.context['regex'],
              }

    if verbosity > 1:
        print 'normalized GET query parameters: %r' % initial

    if request.method == 'POST':
        # GetLagForm only has a GET button
        context['form'] = Form(request.POST)
    elif request.method == 'GET':
        context['form'] = Form(data=initial, initial=initial)

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
        if kwargs.get('field_names'):
            context['field_names'] = kwargs.get('field_names', [])
        else:
            context['field_names'] = list(SLAmodels.Refrefurb._meta.get_all_field_names())
        
    if not context.get('filename'):
        context['filename'] = 'Refurb.csv'

    return context


import re
re_model_instance_dot = re.compile('__|[.]+')


def follow_double_underscores(obj, field_name=None, excel_dialect=True):
    '''Like getattr(obj, field_name) only follows model relationships through "__" or "." as link separators'''
    if not obj:
        return obj
    if isinstance(field_name, list):
        split_fields = field_name
    else:
        split_fields = re_model_instance_dot.split(field_name)
    if len(split_fields) <= 1:

        if hasattr(obj, split_fields[0]):
            value = getattr(obj, split_fields[0])
        elif hasattr(obj, split_fields[0] + '_id'):
            value = getattr(obj, split_fields[0] + '_id')
        elif hasattr(obj, split_fields[0] + '_set'):
            value = getattr(obj, split_fields[0] + '_set')
        elif split_fields[0] in obj.__dict__:
            value = obj.__dict__.get(split_fields[0])
        else:
            return follow_double_underscores(getattr(obj, split_fields[0]), field_name=split_fields[1:])
        if excel_dialect:
            if isinstance(value, datetime.datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S')
        return value
    return follow_double_underscores(getattr(obj, split_fields[0]), field_name=split_fields[1:])


def table_from_list_of_instances(data, field_names=None, excluded_field_names=None, sort=True, excel_dialect=True):
    '''Return an iterator over the model instances that yeilds lists of values

    This forms a table suitable for output as a csv

    FIXME: allow specification of related field values with double_underscore
    '''
    excluded_field_names = excluded_field_names or []
    excluded_field_names += '_state'
    excluded_field_names = set(excluded_field_names)

    for i, row in enumerate(data):
        if not field_names or not any(field_names):
            field_names = [k for (k, v) in row.__dict__.iteritems() if not k in excluded_field_names]
        if not i:
            yield field_names
        yield [follow_double_underscores(row, field_name=k, excel_dialect=True) for k in field_names]


def csv_response_from_context(context=None, filename=None, field_names=None, null_string=''):
    filename = filename or context.get('filename') or 'table_download.csv'
    field_names = context.get('field_names')

    data = context

    # find the data table within the context dict. should be named 'data.cases' or 'data.d3data'
    if not (isinstance(data, (tuple, list)) and isinstance(data[0], (tuple, list))):
        data = json.loads(data.get('data', {}).get('d3data', '[[]]'))
        if not data or not any(data):
            data = context.get('data', {}).get('cases', [[]])

    if not isinstance(data, (list, tuple)) or not isinstance(data[0], (list, tuple)):
        data = table_from_list_of_instances(data, field_names=field_names)

    try:
        if len(data) < len(data[0]):
            data = util.transposed_lists(data)  # list(list(row) for row in data)
    except TypeError:
        # no need to transpose if a generator was provided instead of a list or tuple (anythin with a len attribute)
        pass

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    writer = csv.writer(response)
    for row in data:
        writer.writerow([unicode(s if not s == None else null_string).encode('UTF-8') for s in row])

    return response


# def lag(request, *args):
#     '''Line chart with zoom and pan and "focus area" at bottom like google analytics.
    
#     Data takes a long time to load, so you better use this to increase the timeout
#     python gunicorn bigdata.wsgi:application --bind bigdata.enet.sharplabs.com:8000 --graceful-timeout=60 --timeout=60
#     '''
#     # print 'lag with form'
#     context = context_from_request(request)

#     # retrieve a dict {'refurbs_dict': {}, 'lags_dict': {}, 'means_dict': {}, 'hist': {}, 'pmf': {}, 'cfd': {} ...etc}
#     # each one of these dicts is a dictionary with keys for each of the series/filter definitions (which are used for the legend string)
#     lags_dict = SLAmodels.explore_lags(**context['filter'])
#     context['means'] = lags_dict['means_dict']
#     hist = lags_dict[context['plot']]  # context['plot'] is 'cfd', 'pmf' or 'hist', etc


#     # FIXME: use util.transposed_lists and make this look more like the hist() view below
#     hist_t=[[],[],[],[]]
#     names, xdata, ydata = [], [], []
#     if hist and len(hist) > 1:
#         hist_t = util.transposed_matrix(hist[1:])

#         if hist[0]:
#             # print hist[0]
#             names = hist[0][1:]
#             #print names
#             xdata = hist_t[0]
#             ydata = hist_t[1:]
#     # print names

#     #tooltip_date = "%d %b %Y %H:%M:%S %p"
#     extra_series = {
#                     "tooltip": {"y_start": " ", "y_end": " returns"},
#                    #"date_format": tooltip_date
#                    }

#     chartdata = { 'x': xdata }

#     for i, name in enumerate(names):
#         chartdata['name%d' % (i + 1)] = name
#         chartdata['y%d' % (i + 1)] = ydata[i]
#         chartdata['extra%d' % (i + 1)] = extra_series

#     subtitle = []

#     params = {
#         'FY': context['filter']['fiscal_years'],
#         'Reason': context['filter']['reasons'],
#         'Account #': context['filter']['account_numbers'],
#         'Model #': context['filter']['model_numbers'],
#         }

#     for k, v in params.iteritems():
#         if len(v) == 1 and v[0] and len(str(v[0])):
#             subtitle += [str(k) + ': ' + str(v[0])] 

#     context.update({
#         'data': {
#             'title': 'Returns Lag <font color="gray">' + context['plot_name'] + '</font>',
#             'd3data': json.dumps(util.transposed_lists(hist)),
#             'subtitle': ', '.join(subtitle),
#             'charttype': "lineWithFocusChart",
#             'chartdata': chartdata,
#             'chartcontainer': 'linewithfocuschart_container',
#             'extra': {
#                 'x_is_date': False,
#                 'x_axis_format': ',.0f', # %b %Y %H',
#                 'y_axis_format': ',.0f', # "%d %b %Y"
#                 'tag_script_js': True,
#                 'jquery_on_ready': True,
#                 },
#             }
#         })
#     return render(request, 'miner/lag.html', context)


# def hist(request, *args):
#     '''Multi-column table of lag vs. counts (histogram) displayed as a line plot.'''
#     context = context_from_request(context=None, request=request)

#     lags_dict = SLAmodels.explore_lags(**context['filter'])
#     context['means'] = lags_dict['means_dict']

#     hist_type = context['plot']

#     context.update({'data': {
#         'title': 'Returns Lag <font color="gray">' + hist_type.upper() + '</font>',
#         'xlabel': 'Lag (days)',
#         'ylabel': util.HIST_CONFIG[hist_type]['ylabel'],
#         'd3data': json.dumps(util.transposed_lists(lags_dict[hist_type])),
#         'form': {},
#         }})
#     return render(request, 'miner/hist.html', context)
