# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
#from django.http import HttpResponse
from django.views.generic import View  #, TemplateView
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

# from forms import GetLagForm

from pug.nlp import parse
#from pug.nlp.util import normalize_scientific_notation
#from pug.nlp.character_subset import digits
from pug.nlp import util
from pug.nlp import db


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
            # print path
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


def submit_lag_form(request, f, context, *args):
    '''Line chart with zoom and pan and "focus area" at bottom like google analytics.
    
    Data takes a long time to load, so you better use this to increase the timeout
    python gunicorn bigdata.wsgi:application --bind bigdata.enet.sharplabs.com:8000 --graceful-timeout=60 --timeout=60
    '''
    context['form'] = f

    model_numbers = [s.strip() for s in f.cleaned_data['model'].split(',')]
    fiscal_years = request.GET.getlist('fiscal_years')

    hist_formats = ['hist', 'pmf', 'cdf', 'cmf']
    hist_format = 'cmf'
    if args and len(str(args[0])):
        hist_format_str = str(args[0]).lower().strip()
    if hist_format_str in hist_formats:
        hist_format = hist_format_str

    reasons = request.GET.get('r', 'R').split(',') or ['R']
    account_numbers = request.GET.get('an', '').split(',') or ['']

    params = {
        'FY': fiscal_years,
        'Reason': reasons,
        'Account #': account_numbers,
        'Model #': model_numbers,
        }

    # context['refurbs'] = []
    # for mn in model_numbers:

    #     refurbs = SLARef.objects\
    #            .filter(model__istartswith=mn, pipesale__isnull=False)\
    #            .order_by('recvdat')\
    #            .select_related('refrepeia', 'rano')
    #     # sales = PipeSale.objects\
    #     #        .filter(material__istartswith=mn)\
    #     #        .order_by('billing_doc_date')
    #     # calls = CallMaster.objects\
    #     #        .filter(model__istartswith=mn)\
    #     #        .order_by('start_date_time').values()
    #     context['refurbs'] += list(refurbs)


    # print params
    lags = SLAmodels.explore_lags(fiscal_years=fiscal_years, model_numbers=model_numbers, reasons=reasons, account_numbers=account_numbers, verbosity=1)
    hist = lags[hist_formats.index(hist_format)+1]

    #print hist_formats.index(hist_format)
    #print [max([y[1] for y in x]) for x in lags[1:]]

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

    for k, v in params.iteritems():
        if len(v) == 1 and v[0] and len(str(v[0])):
            subtitle += [str(k) + ': ' + str(v[0])] 


    data0 = util.transposed_lists([
        ['number', 'New York', 'San Francisco','Austin'],
        [1, '63.4', '62.7', '72.2'],
        [2, '58.0', '59.9', '67.7'],
        [3, '53.3', '59.1', '69.4'],
        [4, '55.7', '58.8', '68.0'],
        [5, '64.2', '58.7', '72.4'],
        [6, '58.8', '57.0', '77.0'],
        [7, '57.9', '56.7', '82.3'],
        [8, '61.8', '56.8', '78.9'],
        [9, '69.3', '56.7', '68.8'],
        [10, '71.2', '60.1', '68.7'],
        [11, '68.7', '61.1', '70.3'],
    ])


    context.update({'data': {
        'title': 'Returns Lag <font color="gray">' + hist_format.upper() + '</font>',
        'subtitle': ', '.join(subtitle),
        'charttype': "lineWithFocusChart",
        'chartdata': chartdata,
        'd3data': json.dumps(data0),
        'chartcontainer': 'linewithfocuschart_container',
        'extra': {
            'x_is_date': False,
            'x_axis_format': ',.0f', # %b %Y %H',
            'y_axis_format': ',.0f', # "%d %b %Y"
            'tag_script_js': True,
            'jquery_on_ready': True,
            },
        'form': {},
        }})
    #print context
    return render(request, 'miner/lag.html', context)


def lag(request, *args):
    # print 'lag with form'
    context = {}
    f = GetLagForm()

    if request.method == 'POST':
        f = GetLagForm(request.POST)

    elif request.method == 'GET':
        model = request.GET.get('mn', "") or request.GET.get('model', "")
        initial = {'submit': 'Submit', 'model': model}
        f = GetLagForm(data=initial)  #, initial=initial)

    context['form'] = f
    context['form_is_valid'] = f.is_valid()
    return submit_lag_form(request, f, context, *args)
