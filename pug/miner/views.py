
def url_graph(request, chart_type='lineWithFocusChart', values_list=('call_type'), filter_dict={'model__startswith': 'LC60'}, model='CaseMaster'):
    """
    Send data in the context variable "data" for a pie chart (x, y) and a line chart.
    """

    # graph_uri = r'Origin,3,1_I,2,2_10~Origin_II,2~I_III~I_IV~II_IV~IV_V~V_I~VI_V,.5,3~VII,.2,4_V'
    data = {
        'graph_uri': '~'.join(quote(source) + '_' + quote(target) for source, target in node_pairs),
        }
    return render_to_response('miner/home.html', data)

def connections(request, edges):
    """
    Plot a force-directed graph based on the edges provided
    """
    edge_list, node_list = parse_graph_definition(edges)
    data = {'nodes': json.dumps(node_list), 'edges': json.dumps(edge_list)}
    return render_to_response('call_center/connections.html', data)

def parse_node_name(name, use_defaults=False):
    """
    >>> sorted(parse_node_name('Origin,2.7, 3 ')[1].items())
    [('charge', 2.7), ('group', 3), ('name', 'Origin')]
    >>> parse_node_name('Origin,2.7, 3 ')[0]
    'Origin'
    """
    # if the name is not a string, but a dict defining a node, then just set the defaults and return it
    if isinstance(name, Mapping):
        ans = dict(name)
        for j, field in enumerate(parse_node_name.schema):
            if field['key'] not in ans:
                ans[field['key']] = field['default']
        return ans
    seq = listify(name, delim=',')
    ans = {}
    for j, field in enumerate(parse_node_name.schema):
        if 'default' in field:
            try:
                ans[field['key']] = field['type'](seq[j])
            except:
                if use_defaults:
                    ans[field['key']] = field['default']
        else:
            try:
                ans[field['key']] = ans.get(field['key'], field['type'](seq[j]))
            except:
                pass
    return ans
parse_node_name.schema = (
                {'key': 'name', 'type': str},  # TODO: use the absence of a default value (rather than index > 0) to identify mandatory fields
                {'key': 'charge', 'type': float, 'default': 1},
                {'key': 'group', 'type': intify, 'default': 0},  # TODO: this should be a string like the names/indexes to nodes (groups are just hidden nodes)
              )
