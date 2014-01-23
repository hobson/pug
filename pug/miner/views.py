from django.shortcuts import render

def url_graph(request, chart_type='lineWithFocusChart', values_list=('call_type'), filter_dict={'model__startswith': 'LC60'}, model='CaseMaster'):
    """
    Send data in the context variable "data" for a pie chart (x, y) and a line chart.
    """

    # graph_uri = r'Origin,3,1_I,2,2_10~Origin_II,2~I_III~I_IV~II_IV~IV_V~V_I~VI_V,.5,3~VII,.2,4_V'
    data = {
        'graph_uri': '~'.join(quote(source) + '_' + quote(target) for source, target in node_pairs),
        }
    return render_to_response('miner/home.html', data)