# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
#from django.http import HttpResponse
from django.views.generic import View  #, TemplateView
from django.template import Context
from django.template.response import TemplateResponse #, HttpResponse
from django.template.loader import get_template
from django.http import Http404
from django import http
from django.utils import simplejson as json

# from sec_sharp_refurb.models import Refrefurb as SECRef
import call_center.models as SLAmodels


import os
from django.shortcuts import render
from forms import GetLagForm

from pug.nlp import parse
#from pug.nlp.util import normalize_scientific_notation
#from pug.nlp.character_subset import digits
from pug.nlp import util
from pug.nlp import db


# format options for lag histograms:
#   hist = ff = fd = Frequency Distribution/Function (histogram of counts)
#   pmf = pdf = Probability Mass/Distribution Function (or PDF, probability distribution/density function)
#   cmf = cdf = Cumulative Distribution/Mass Function (cumulative probability)
#   cfd = cff = Cumulative Frequency Distribution/Function (cumulative counts)


#from Returns import tv_lags

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


def context_from_request(request, context=None, Form=GetLagForm, delim=','):
    if context is None:
        context = Context()

    context['filter'] = {}

    limit = request.GET.get('limit', "") or request.GET.get('num', "") or request.GET.get('num_rows', "") or request.GET.get('rows', "") or request.GET.get('records', "") or request.GET.get('count', "")
    context['limit'] = util.make_int(limit)

    mn = request.GET.get('mn', "") or request.GET.get('model', "") or request.GET.get('models', "") or request.GET.get('model_number', "") or request.GET.get('model_numbers', "")
    mn = [s.strip() for s in mn.split(',')] or ['']
    context['filter']['model_numbers'] = mn

    sn = request.GET.get('sn', "") or request.GET.get('serial', "") or request.GET.get('serials', "") or request.GET.get('serial_number', "") or request.GET.get('serial_numbers', "")
    sn = [s.strip() for s in sn.split(',')] or ['']   
    context['filter']['serial_numbers'] = sn

    fy = request.GET.get('fy', "") or request.GET.get('yr', "") or request.GET.get('year', "") or request.GET.get('years', "") or request.GET.get('fiscal_year', "") or request.GET.get('fiscal_years', "")
    fiscal_years = [util.normalize_year(y) for y in fy.split(',')] or []
    fiscal_years = [str(y) for y in fiscal_years if y]
    context['filter']['fiscal_years'] = fiscal_years

    r = request.GET.get('r', "") or request.GET.get('rc', "") or request.GET.get('rcode', "") or request.GET.get('reason', "") or request.GET.get('reasons', "")
    r = [s.strip() for s in r.split(',')] or ['']
    context['filter']['reasons'] = r

    a = request.GET.get('a', "") or request.GET.get('an', "") or request.GET.get('account', "") or request.GET.get('account_number', "") or request.GET.get('account_numbers', "")
    a = [s.strip() for s in a.split(',')] or ['']
    context['filter']['account_numbers'] = a

    min_dates = request.GET.get('min_date', "") or request.GET.get('min_dates', "")
    min_dates = [s.strip() for s in min_dates.split(',')] or ['']
    context['filter']['min_dates'] = min_dates

    max_dates = request.GET.get('max_date', "") or request.GET.get('max_dates', "")
    max_dates = [s.strip() for s in max_dates.split(',')] or ['']
    context['filter']['max_dates'] = max_dates

    series_name = request.GET.get('s', "") or request.GET.get('n', "") or request.GET.get('series', "") or request.GET.get('name', "")
    filter_values = series_name.split(' ')
    if filter_values and len(filter_values)==4:
        mn = [filter_values[0].strip('*')]
        r = [filter_values[1].strip('*')]
        a = [filter_values[2].strip('*')]
        fiscal_years = [filter_values[3].strip('*')]

    lag_days = int(request.GET.get('lag', None) or 365)
    max_lag = int(request.GET.get('max_lag', None) or lag_days)
    min_lag = int(request.GET.get('min_lag', None) or (lag_days - 1))

    initial = {'model': ', '.join(context['filter']['model_numbers']), 
               'serial': ', '.join(context['filter']['serial_numbers']),
               'reason': ', '.join(context['filter']['reasons']),
               'account': ', '.join(context['filter']['account_numbers']),
               'fiscal_years': ', '.join(context['filter']['fiscal_years']),
               'min_lag': str(min_lag),
               'max_lag': str(max_lag),
               'min_date': ', '.join(context['filter']['min_dates']),
               'max_date': ', '.join(context['filter']['max_dates'])
              }

    # this can never happen since Form only has a GET button
    if request.method == 'POST':
        context['form'] = Form(request.POST)
    elif request.method == 'GET':
        context['form'] = Form(data=util.update_dict(initial, {'submit': 'Submit'}, copy=True), initial=initial)

    context['form_is_valid'] = context['form'].is_valid()

    return context


def context_from_args(args=None, context=None):
    if context is None:
        context = Context()

    context['hist_format'] = util.HIST_NAME['cfd']
    if args and len(str(args[0])):
        context['hist_format'] = util.HIST_NAME.get(str(args[0]).lower().strip(), context['hist_format'])
        context['hist_name'] = util.HIST_CONFIG[context['hist_format']]['name']

    return context


def lag(request, *args):
    '''Line chart with zoom and pan and "focus area" at bottom like google analytics.
    
    Data takes a long time to load, so you better use this to increase the timeout
    python gunicorn bigdata.wsgi:application --bind bigdata.enet.sharplabs.com:8000 --graceful-timeout=60 --timeout=60
    '''
    # print 'lag with form'
    context = context_from_request(request)
    context = context_from_args(context=context, args=args)

    lags = SLAmodels.explore_lags(**context['filter'])
    hist = lags[context['hist_format']]

    # FIXME: use util.transposed_lists and make this look more like the hist() view below
    hist_t=[[],[],[],[]]
    names, xdata, ydata = [], [], []
    if hist and len(hist) > 1:
        hist_t = util.transposed_matrix(hist[1:])

        if hist[0]:
            # print hist[0]
            names = hist[0][1:]
            #print names
            xdata = hist_t[0]
            ydata = hist_t[1:]
    # print names

    #tooltip_date = "%d %b %Y %H:%M:%S %p"
    extra_series = {"tooltip": {"y_start": " ", "y_end": " returns"},
                   #"date_format": tooltip_date
                   }

    chartdata = { 'x': xdata }

    for i, name in enumerate(names):
        chartdata['name%d' % (i + 1)] = name
        chartdata['y%d' % (i + 1)] = ydata[i]
        chartdata['extra%d' % (i + 1)] = extra_series

    subtitle = []

    params = {
        'FY': context['fiscal_years'],
        'Reason': context['reasons'],
        'Account #': context['account_numbers'],
        'Model #': context['model_numbers'],
        }

    for k, v in params.iteritems():
        if len(v) == 1 and v[0] and len(str(v[0])):
            subtitle += [str(k) + ': ' + str(v[0])] 

    context.update({
        'data': {
            'title': 'Returns Lag <font color="gray">' + context['hist_format'].upper() + '</font>',
            'd3data': json.dumps(util.transposed_lists(hist)),
            'subtitle': ', '.join(subtitle),
            'charttype': "lineWithFocusChart",
            'chartdata': chartdata,
            'chartcontainer': 'linewithfocuschart_container',
            'extra': {
                'x_is_date': False,
                'x_axis_format': ',.0f', # %b %Y %H',
                'y_axis_format': ',.0f', # "%d %b %Y"
                'tag_script_js': True,
                'jquery_on_ready': True,
                },
            }
        })
    return render(request, 'miner/lag.html', context)


def hist(request, *args):
    '''Multi-column table of lag vs. counts (histogram) displayed as a line plot.'''
    context = context_from_request(context=None, request=request)
    context = context_from_args(context=context, args=args)

    # print params
    lags = SLAmodels.explore_lags(**context['filter'])
    hist_name = context['hist_format']

    context.update({'data': {
        'title': 'Returns Lag <font color="gray">' + hist_name.upper() + '</font>',
        'xlabel': 'Lag (days)',
        'ylabel': util.HIST_CONFIG[hist_name]['ylabel'],
        'd3data': json.dumps(util.transposed_lists(lags[hist_name])),
        'form': {},
        }})
    return render(request, 'miner/hist.html', context)
